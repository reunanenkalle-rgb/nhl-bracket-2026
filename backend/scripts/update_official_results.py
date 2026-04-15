# backend/scripts/update_official_results.py

import sys
import os
import time
import traceback
import requests
import json

# --- Path Setup ---
# Add parent directory (backend) to sys.path to allow importing 'app' and 'models'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)  # Insert at the beginning

# --- Application Imports ---
try:
    from app import app  # For app context and config
    from models import db, Team, Series  # For database models
except ImportError as e:
    print(
        f"Error importing Flask app or models: {e}. \n"
        f"Ensure this script is in the 'backend/scripts' directory and the main app files are in 'backend/'.\n"
        f"Current sys.path: {sys.path}"
    )
    traceback.print_exc()
    sys.exit(1)

# --- Configuration ---
SEASON_TO_FETCH = "20252026"
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
    except Exception as e:
        print(f"Error fetching or decoding data from NHL API: {e}")
        if "response" in locals() and response is not None:  # Check if response exists
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

                # Wrap processing of a single API series in a try-except
                try:
                    top_seed_api_info = api_series_details.get("topSeed", {})
                    bottom_seed_api_info = api_series_details.get("bottomSeed", {})

                    api_top_seed_abbr = top_seed_api_info.get("abbrev")
                    api_top_seed_id_carousel = top_seed_api_info.get("id")
                    api_top_seed_wins = top_seed_api_info.get("wins", 0)

                    api_bottom_seed_abbr = bottom_seed_api_info.get("abbrev")
                    api_bottom_seed_id_carousel = bottom_seed_api_info.get("id")
                    api_bottom_seed_wins = bottom_seed_api_info.get("wins", 0)

                    if not api_top_seed_abbr or not api_bottom_seed_abbr:
                        print(
                            f"  Warning: API data for series '{series_letter}' (DB: {db_series_identifier}) is missing team abbreviations. Skipping this series instance."
                        )
                        errors_count += (
                            1  # Count as an error for this series processing
                        )
                        continue

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
                        errors_count += 1
                        continue

                    teams_were_updated_in_db = False
                    if (
                        db_series.round_number > 0
                    ):  # Check if teams in DB need to be set (for R2+ mostly)
                        # Standard way to assign Top Seed to Team1, Bottom Seed to Team2 if both are unset
                        if db_series.team1_id is None and db_series.team2_id is None:
                            db_series.team1_id = db_team_obj_api_top.id
                            db_series.team2_id = db_team_obj_api_bottom.id
                            teams_were_updated_in_db = True
                            print(
                                f"    Set teams for '{db_series_identifier}': {db_team_obj_api_top.abbreviation} (as T1) vs {db_team_obj_api_bottom.abbreviation} (as T2)"
                            )
                        # If one team is set, set the other if it's different and available
                        elif db_series.team1_id is None and (
                            db_series.team2_id != db_team_obj_api_top.id
                            if db_series.team2_id
                            else True
                        ):
                            db_series.team1_id = db_team_obj_api_top.id
                            teams_were_updated_in_db = True
                            print(
                                f"    Set team1 for '{db_series_identifier}' to {db_team_obj_api_top.abbreviation}"
                            )
                        elif db_series.team2_id is None and (
                            db_series.team1_id != db_team_obj_api_bottom.id
                            if db_series.team1_id
                            else True
                        ):
                            db_series.team2_id = db_team_obj_api_bottom.id
                            teams_were_updated_in_db = True
                            print(
                                f"    Set team2 for '{db_series_identifier}' to {db_team_obj_api_bottom.abbreviation}"
                            )

                        if teams_were_updated_in_db:
                            teams_assigned_to_series_count += 1
                            # Flush to ensure subsequent .team1 and .team2 relationships are fresh if IDs were just set.
                            # This helps if the relationships aren't automatically updated before access.
                            db.session.flush()

                    db_series_team1 = db_series.team1
                    db_series_team2 = db_series.team2

                    if not db_series_team1 or not db_series_team2:
                        print(
                            f"  ERROR: Teams for series '{db_series_identifier}' (Round {db_series.round_number}) are not set in DB. Cannot assign wins."
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
                        # This occurs if db_series.team1 is neither API top nor bottom seed.
                        # This implies the mapping of API top/bottom to db.team1/team2 established
                        # when setting TBD teams was different from this game's top/bottom.
                        # A robust solution checks if db_series.team2 matches one of them.
                        if (
                            db_series_team2.abbreviation == api_top_seed_abbr
                        ):  # db_series.team2 is API topSeed
                            db_series.games_team2_won = api_top_seed_wins
                            db_series.games_team1_won = api_bottom_seed_wins  # so db_series.team1 must be API bottomSeed
                        elif (
                            db_series_team2.abbreviation == api_bottom_seed_abbr
                        ):  # db_series.team2 is API bottomSeed
                            db_series.games_team2_won = api_bottom_seed_wins
                            db_series.games_team1_won = api_top_seed_wins  # so db_series.team1 must be API topSeed
                        else:
                            print(
                                f"  CRITICAL MISMATCH: For DB series '{db_series_identifier}' ({db_series_team1.abbreviation} vs {db_series_team2.abbreviation}), "
                                f"API reports teams '{api_top_seed_abbr}' vs '{api_bottom_seed_abbr}'. Cannot reliably assign scores from this record."
                            )
                            errors_count += 1
                            # Potentially skip updating scores for this series to avoid bad data
                            # For now, we'll let it proceed to status determination which might default to PENDING.
                            # continue # Uncomment to skip this series if scores can't be mapped.

                    # Update status and actual winner
                    api_winning_team_carousel_id = api_series_details.get(
                        "winningTeamId"
                    )

                    db_series.actual_winner_team_id = (
                        None  # Reset for each processing pass
                    )
                    db_series.status = "PENDING"  # Default to PENDING

                    if api_winning_team_carousel_id:
                        db_series.status = "COMPLETED"
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

                    # If API doesn't declare a winner, check our game counts
                    # This logic now correctly comes *after* checking the API's explicit winner
                    # And ensures status is COMPLETED only if 4 wins are reached AND API didn't already say so.
                    if (
                        db_series.status != "COMPLETED"
                    ):  # Only if not already marked complete by API
                        if db_series.games_team1_won == 4:
                            db_series.status = "COMPLETED"
                            db_series.actual_winner_team_id = db_series.team1_id
                            if db_series.team1_id:
                                db_series.actual_winner_team_id = db_series.team1_id
                            else:  # Should ideally not happen if teams are set
                                print(
                                    f"  Warning: Series {db_series_identifier} team1_id is None, cannot set derived winner based on games_team1_won."
                                )
                        elif db_series.games_team2_won == 4:
                            db_series.status = "COMPLETED"
                            db_series.actual_winner_team_id = db_series.team2_id
                            if db_series.team2_id:
                                db_series.actual_winner_team_id = db_series.team2_id
                            else:  # Should ideally not happen
                                print(
                                    f"  Warning: Series {db_series_identifier} team2_id is None, cannot set derived winner based on games_team2_won."
                                )
                    # --- NEW LOGIC FOR 2026 SERIES LENGTH ---
                    if db_series.status == "COMPLETED":
                        # In a best-of-7, length is simply the sum of all games played.
                        # Since one team must have 4 wins to complete the series,
                        # this will correctly result in 4, 5, 6, or 7.
                        db_series.actual_series_length = (
                            db_series.games_team1_won + db_series.games_team2_won
                        )
                    else:
                        # Reset to None if the series is reset or still in progress
                        db_series.actual_series_length = None
                    # ----------------------------------------

                    # If still not completed, check if active
                    if db_series.status != "COMPLETED":
                        if (
                            db_series.games_team1_won is not None
                            and db_series.games_team1_won > 0
                        ) or (
                            db_series.games_team2_won is not None
                            and db_series.games_team2_won > 0
                        ):
                            db_series.status = "ACTIVE"
                            # db_series.actual_winner_team_id remains None (already reset)
                        else:  # No wins yet, could be PENDING (already default)
                            # db_series.status = "PENDING"; # Already default
                            db_series.actual_winner_team_id = None

                    # This print and counter should be outside the status determination logic,
                    # but inside the try block for processing a single series.
                    print(
                        f"  Processed Series: {db_series.series_identifier} (API: {series_letter}) R:{db_series.round_number} - "
                        f"{db_series_team1.abbreviation if db_series_team1 else 'TBD'} ({db_series.games_team1_won if db_series.games_team1_won is not None else 'N/A'}) vs "
                        f"{db_series_team2.abbreviation if db_series_team2 else 'TBD'} ({db_series.games_team2_won if db_series.games_team2_won is not None else 'N/A'}) - Status: {db_series.status}"
                    )
                    updated_series_count += 1

                except (
                    Exception
                ) as series_err:  # This except matches the try for a single series_details
                    print(
                        f"  Error processing API series details for '{series_letter}' (DB ID: '{db_series_identifier}'): {series_err}"
                    )
                    traceback.print_exc()
                    errors_count += 1

        # Commit block after processing all series in all rounds
        if (
            updated_series_count > 0
            or teams_assigned_to_series_count > 0
            or errors_count
            > 0  # Commit even if there were errors to save partial successes or rollbacks from errors
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
            print(
                f"Encountered {errors_count} errors during individual series processing."
            )


if __name__ == "__main__":
    with app.app_context():
        print(
            "Ensuring database tables are created (from update_official_results.py)..."
        )
        db.create_all()
        print("Database tables checked.")

    fetch_and_update_playoff_results()
    print("\n--- Playoff results update script finished ---")
