# backend/scripts/update_official_results.py

import sys
import os
import time
import traceback
import requests
import json

# Add parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from app import app, db, Team, Series
except ImportError as e:
    print(
        f"Error importing Flask app/models: {e}. Ensure script is runnable and paths are correct."
    )
    sys.exit(1)

# --- Configuration ---
SEASON_TO_FETCH = "20242025"
API_BASE_URL = "https://api-web.nhle.com"
API_ENDPOINT = f"/v1/playoff-series/carousel/{SEASON_TO_FETCH}/"

# --- Mapping API Series Letter to your DB Series Identifiers ---
API_SERIES_LETTER_TO_DB_MAP: dict[str, str] = {
    "A": "EC_R1_M1",
    "B": "EC_R1_M2",
    "C": "EC_R1_M3",
    "D": "EC_R1_M4",
    "E": "WC_R1_M1",
    "F": "WC_R1_M2",
    "G": "WC_R1_M3",
    "H": "WC_R1_M4",
    "I": "EC_R2_M1",
    "J": "EC_R2_M2",
    "K": "WC_R2_M1",
    "L": "WC_R2_M2",
    "M": "EC_R3_CF",
    "N": "WC_R3_CF",
    "O": "SCF",  # Assuming 'O' for Stanley Cup Final if API follows A-N for first 3 rounds
}


def fetch_and_update_playoff_results():
    full_api_url = f"{API_BASE_URL}{API_ENDPOINT}"
    print(f"Fetching playoff series data from: {full_api_url}")

    try:
        response = requests.get(full_api_url, timeout=15)
        response.raise_for_status()
        api_data = response.json()
        print("Successfully fetched data from NHL carousel API.")
    except Exception as e:  # Catching generic exception for requests and json decoding
        print(f"Error fetching or decoding data from NHL API: {e}")
        if "response" in locals() and response is not None:
            print(f"Response text (first 500 chars): {response.text[:500]}...")
        traceback.print_exc()
        return

    if (
        not api_data
        or "rounds" not in api_data
        or not isinstance(api_data["rounds"], list)
    ):
        print("API response is missing 'rounds' data or is not in expected format.")
        return

    with app.app_context():
        print("\nProcessing API data and updating database...")
        updated_series_count = 0
        teams_assigned_to_series_count = 0
        errors_count = 0

        for round_data in api_data["rounds"]:
            if "series" not in round_data or not isinstance(round_data["series"], list):
                continue

            api_round_number = round_data.get("roundNumber")

            for api_series_details in round_data["series"]:
                series_letter = api_series_details.get("seriesLetter")
                db_series_identifier = API_SERIES_LETTER_TO_DB_MAP.get(series_letter)

                if not db_series_identifier:
                    print(
                        f"  Warning: No mapping found for API series letter '{series_letter}' (Round {api_round_number}). Skipping."
                    )
                    continue

                db_series = Series.query.filter_by(
                    series_identifier=db_series_identifier
                ).first()
                if not db_series:
                    print(
                        f"  Warning: Series '{db_series_identifier}' (mapped from API series '{series_letter}') not found in database. Skipping."
                    )
                    continue

                try:
                    top_seed_api_info = api_series_details.get("topSeed", {})
                    bottom_seed_api_info = api_series_details.get("bottomSeed", {})

                    api_top_seed_abbr = top_seed_api_info.get("abbrev")
                    api_top_seed_id_carousel = top_seed_api_info.get(
                        "id"
                    )  # API's own ID for this team
                    api_top_seed_wins = top_seed_api_info.get("wins", 0)

                    api_bottom_seed_abbr = bottom_seed_api_info.get("abbrev")
                    api_bottom_seed_id_carousel = bottom_seed_api_info.get(
                        "id"
                    )  # API's own ID
                    api_bottom_seed_wins = bottom_seed_api_info.get("wins", 0)

                    if not api_top_seed_abbr or not api_bottom_seed_abbr:
                        print(
                            f"  Warning: API data for series '{series_letter}' (DB: {db_series_identifier}) is missing team abbreviations. Skipping."
                        )
                        continue

                    # Get DB Team objects using their abbreviations
                    db_team_obj_api_top = Team.query.filter_by(
                        abbreviation=api_top_seed_abbr
                    ).first()
                    db_team_obj_api_bottom = Team.query.filter_by(
                        abbreviation=api_bottom_seed_abbr
                    ).first()

                    if not db_team_obj_api_top or not db_team_obj_api_bottom:
                        print(
                            f"  Warning: Could not find one or both teams ('{api_top_seed_abbr}', '{api_bottom_seed_abbr}') in DB by abbreviation for series '{db_series_identifier}'. Skipping this series update."
                        )
                        continue

                    # --- Update teams for later rounds if they were TBD in DB ---
                    teams_were_updated_in_db = False
                    if (
                        db_series.round_number > 0
                    ):  # Applicable to all rounds if seeding could be incomplete
                        if db_series.team1_id is None and db_series.team2_id is None:
                            # Assign API's top seed to DB's team1, bottom seed to DB's team2
                            # This assignment order matters for games_team1_won vs games_team2_won later
                            db_series.team1_id = db_team_obj_api_top.id
                            db_series.team2_id = db_team_obj_api_bottom.id
                            teams_were_updated_in_db = True
                            print(
                                f"    Set teams for '{db_series_identifier}': {db_team_obj_api_top.abbreviation} (as T1) vs {db_team_obj_api_bottom.abbreviation} (as T2)"
                            )
                        elif (
                            db_series.team1_id is None
                            and db_series.team2_id != db_team_obj_api_top.id
                        ):
                            db_series.team1_id = (
                                db_team_obj_api_top.id
                            )  # Assuming top seed fills first available TBD slot
                            teams_were_updated_in_db = True
                            print(
                                f"    Set team1 for '{db_series_identifier}' to {db_team_obj_api_top.abbreviation}"
                            )
                        elif (
                            db_series.team2_id is None
                            and db_series.team1_id != db_team_obj_api_bottom.id
                        ):
                            db_series.team2_id = (
                                db_team_obj_api_bottom.id
                            )  # Assuming bottom seed fills second TBD
                            teams_were_updated_in_db = True
                            print(
                                f"    Set team2 for '{db_series_identifier}' to {db_team_obj_api_bottom.abbreviation}"
                            )

                        if teams_were_updated_in_db:
                            teams_assigned_to_series_count += 1
                            # Important: If we just set teams, commit to get relationships updated before proceeding
                            # However, this is inefficient. Better to reload relationship or ensure IDs are used carefully.
                            # For now, we'll rely on the re-fetched db_series.team1 and db_series.team2 below.
                            # If this causes issues, a db.session.flush() + refresh(db_series) might be needed here.

                    # Fetch the series' teams as defined in *our* database
                    # These might have just been updated above for R2+
                    db_series_team1 = db_series.team1
                    db_series_team2 = db_series.team2

                    if not db_series_team1 or not db_series_team2:
                        print(
                            f"  ERROR: Teams for series '{db_series_identifier}' (Round {db_series.round_number}) "
                            f"are not set in DB, even after attempting to populate. Cannot assign wins."
                        )
                        errors_count += 1
                        continue

                    # Assign wins based on matching abbreviations
                    if db_series_team1.abbreviation == api_top_seed_abbr:
                        db_series.games_team1_won = api_top_seed_wins
                        db_series.games_team2_won = api_bottom_seed_wins
                    elif db_series_team1.abbreviation == api_bottom_seed_abbr:
                        db_series.games_team1_won = api_bottom_seed_wins
                        db_series.games_team2_won = api_top_seed_wins
                    else:
                        # This means the teams in the DB for this series_identifier do not match
                        # the teams the API carousel says are in this seriesLetter slot.
                        # This could happen if your API_SERIES_LETTER_TO_DB_MAP is wrong,
                        # or if your initial seeding of team1/team2 for R1 was different from API's top/bottom.
                        print(
                            f"  CRITICAL MISMATCH: For DB series '{db_series_identifier}' ({db_series_team1.abbreviation} vs {db_series_team2.abbreviation}), "
                            f"API reports teams '{api_top_seed_abbr}' vs '{api_bottom_seed_abbr}'. Cannot reliably assign scores."
                        )
                        errors_count += 1
                        continue  # Skip score update for this series to avoid incorrect data

                    # Update status and actual winner
                    api_winning_team_carousel_id = api_series_details.get(
                        "winningTeamId"
                    )
                    if api_winning_team_carousel_id:
                        db_series.status = "COMPLETED"
                        # Determine winning abbreviation from API data
                        winning_abbr_from_api = None
                        if api_winning_team_carousel_id == api_top_seed_id_carousel:
                            winning_abbr_from_api = api_top_seed_abbr
                        elif (
                            api_winning_team_carousel_id == api_bottom_seed_id_carousel
                        ):
                            winning_abbr_from_api = api_bottom_seed_abbr

                        if winning_abbr_from_api:
                            winner_db_team = Team.query.filter_by(
                                abbreviation=winning_abbr_from_api
                            ).first()
                            if winner_db_team:
                                db_series.actual_winner_team_id = winner_db_team.id
                            else:
                                print(
                                    f"  Warning: Winning team abbreviation '{winning_abbr_from_api}' for series '{db_series_identifier}' not found in local DB Team table."
                                )
                        else:
                            print(
                                f"  Warning: Could not determine winning team abbreviation from API winning ID {api_winning_team_carousel_id} for series '{db_series_identifier}'."
                            )
                    elif db_series.games_team1_won > 0 or db_series.games_team2_won > 0:
                        db_series.status = "ACTIVE"
                    else:  # No wins recorded yet, but teams might be set for R1
                        db_series.status = "PENDING"

                    print(
                        f"  Processed Series: {db_series.series_identifier} (API: {series_letter}) R:{db_series.round_number} - "
                        f"{db_series_team1.abbreviation} ({db_series.games_team1_won}) vs "
                        f"{db_series_team2.abbreviation} ({db_series.games_team2_won}) - Status: {db_series.status}"
                    )
                    updated_series_count += 1

                except Exception as series_err:
                    print(
                        f"  Error processing API series '{series_letter}' (DB ID: '{db_series_identifier}'): {series_err}"
                    )
                    traceback.print_exc()
                    errors_count += 1

        if (
            updated_series_count > 0
            or teams_assigned_to_series_count > 0
            or errors_count > 0
        ):
            try:
                db.session.commit()
                print(f"\nDatabase commit successful.")
                print(f"Series results updated: {updated_series_count}")
                if teams_assigned_to_series_count > 0:
                    print(
                        f"Teams newly assigned to series slots: {teams_assigned_to_series_count}"
                    )
            except Exception as e:
                db.session.rollback()
                print(f"Error committing series updates to database: {e}")
                traceback.print_exc()
        else:
            print("\nNo series data was changed or added to the database.")

        if errors_count > 0:
            print(f"Encountered {errors_count} errors during processing.")


if __name__ == "__main__":
    with app.app_context():
        print(
            "Ensuring database tables are created (from update_official_results.py)..."
        )
        db.create_all()
        print("Database tables checked.")

    fetch_and_update_playoff_results()
    print("\n--- Playoff results update script finished ---")
