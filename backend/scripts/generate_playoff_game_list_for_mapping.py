# backend/scripts/generate_playoff_game_list_for_mapping.py

import json
import os
import sys
import time
import traceback

try:
    from nhlpy import NHLClient
except ImportError:
    print("--------------------------------------------------------------------")
    print("ERROR: The 'nhlpy' library was not found.")
    print("Please ensure it is installed in your Python environment.")
    print("You can typically install it using: pip install nhlpy")
    print("--------------------------------------------------------------------")
    sys.exit(1)

# --- Configuration ---
SEASON_TO_FETCH = "20242025"  # For the Spring 2025 Playoffs
PLAYOFF_GAME_TYPE_ID = 3
OUTPUT_DIR = "fetched_data_inspection"  # Directory to save the inspection file
OUTPUT_FILENAME = os.path.join(
    OUTPUT_DIR, f"playoff_games_for_mapping_{SEASON_TO_FETCH}.json"
)


def parse_nhl_playoff_game_id(game_id_int: int) -> dict | None:
    """
    Parses a standard NHL playoff game ID (e.g., 2024030151)
    Assumes format YYYY030RSG where:
    YYYY = season start year (e.g. 2024)
    030  = playoff indicator part
    R    = Round (1-4)
    S    = Series Index within that round (e.g., 1-8 for R1, 1-4 for R2, etc. This is API's index)
    G    = Game number in series (1-7)
    Returns None if format is unexpected.
    """
    s = str(game_id_int)
    if len(s) == 10 and s[4:7] == "030":
        try:
            return {
                "round": int(s[7]),
                "api_series_idx": int(s[8]),  # API's index for the series in that round
                "game_in_series": int(s[9]),
            }
        except ValueError:
            print(
                f"    Warning: Could not parse digits for R, S, or G in game ID {game_id_int}."
            )
            return None
    else:
        # This print can be noisy if there are other game ID formats (e.g. pre-season)
        # print(f"    Info: Game ID {game_id_int} does not match expected playoff format YYYY030RSG for parsing.")
        return None  # Not necessarily an error, could be a different type of playoff game ID if NHL changes format


def fetch_game_list_for_series_mapping():
    """
    Fetches all playoff games for a season, extracts key info for series mapping,
    and saves it to a JSON file.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir_path = os.path.join(script_dir, OUTPUT_DIR)
    os.makedirs(output_dir_path, exist_ok=True)

    output_filepath = os.path.join(output_dir_path, os.path.basename(OUTPUT_FILENAME))
    print(f"Output will be saved to: {output_filepath}")

    print("\nInitializing NHLClient...")
    try:
        client = NHLClient(verbose=False)
        print("NHLClient initialized successfully.")
    except Exception as e:
        print(f"Fatal Error: Could not initialize NHLClient: {e}")
        traceback.print_exc()
        return

    print(f"\nFetching ALL PLAYOFF game IDs for {SEASON_TO_FETCH}...")
    all_playoff_game_ids = []
    try:
        all_playoff_game_ids = client.helpers.get_gameids_by_season(
            SEASON_TO_FETCH, game_types=[PLAYOFF_GAME_TYPE_ID]
        )
        if isinstance(all_playoff_game_ids, list) and len(all_playoff_game_ids) > 0:
            print(
                f"  Found {len(all_playoff_game_ids)} total playoff game IDs for {SEASON_TO_FETCH}."
            )
        elif isinstance(all_playoff_game_ids, list):
            print(
                f"  Warning: Found 0 playoff game IDs for season {SEASON_TO_FETCH}. Cannot generate mapping list."
            )
            return
        else:
            print(
                f"  Warning: Received unexpected type {type(all_playoff_game_ids)} when fetching game IDs."
            )
            return
    except Exception as e:
        print(f"  Error fetching playoff game IDs: {e}")
        traceback.print_exc()
        return

    if not all_playoff_game_ids:
        print("No playoff game IDs to process. Exiting.")
        return

    extracted_games_for_mapping = []
    processed_count = 0
    error_count = 0
    total_to_fetch = len(all_playoff_game_ids)

    print(
        f"\nStarting to fetch boxscores for {total_to_fetch} playoff games to extract mapping info..."
    )
    for game_id in all_playoff_game_ids:
        processed_count += 1
        if (
            processed_count % 20 == 0 or processed_count == total_to_fetch
        ):  # Print progress less frequently
            print(
                f"  Processing game {processed_count}/{total_to_fetch} (ID: {game_id})..."
            )
        try:
            box_score_data = client.game_center.boxscore(game_id=game_id)

            if box_score_data and isinstance(box_score_data, dict):
                game_date = box_score_data.get("gameDate")
                home_team_data = box_score_data.get("homeTeam", {})
                away_team_data = box_score_data.get("awayTeam", {})
                home_abbr = home_team_data.get("abbrev")
                away_abbr = away_team_data.get("abbrev")

                parsed_id_info = parse_nhl_playoff_game_id(game_id)

                if all([game_date, home_abbr, away_abbr]) and parsed_id_info:
                    extracted_games_for_mapping.append(
                        {
                            "game_id": game_id,
                            "date": game_date,
                            "round": parsed_id_info["round"],
                            "api_series_idx": parsed_id_info[
                                "api_series_idx"
                            ],  # API's internal series index for that round
                            "game_num_in_series": parsed_id_info["game_in_series"],
                            "home_team_abbr": home_abbr,
                            "away_team_abbr": away_abbr,
                        }
                    )
                elif not parsed_id_info:
                    print(
                        f"  -> Game ID {game_id}: Could not parse round/series from game ID. Boxscore fetched but not added to mapping list."
                    )
                    # Still log the teams if available for manual checking
                    if home_abbr and away_abbr:
                        print(
                            f"     Teams involved: {home_abbr} vs {away_abbr} on {game_date}"
                        )
                else:  # Missing other essential data like date or team abbrevs
                    print(
                        f"  -> Game ID {game_id}: Missing date or team abbreviations in boxscore. Not added to mapping list."
                    )

            else:
                print(
                    f"  -> Warning: No boxscore data returned by nhlpy for game ID {game_id}."
                )
                error_count += 1

            time.sleep(0.5)  # Be polite to the API
        except Exception as e:
            print(f"  -> ERROR fetching/processing boxscore for game ID {game_id}: {e}")
            # traceback.print_exc() # Can be very verbose, enable if needed for deep debugging
            error_count += 1
            time.sleep(1.0)

    print(f"\nFinished processing games for mapping info.")
    print(f"Successfully extracted info for: {len(extracted_games_for_mapping)} games.")
    if error_count > 0:
        print(f"Encountered errors/missing data for: {error_count} games.")

    if not extracted_games_for_mapping:
        print("No game data for mapping was successfully extracted. Nothing to save.")
        return

    # Sort the data for easier manual review: by round, then by API series index, then by game number
    extracted_games_for_mapping.sort(
        key=lambda x: (x["round"], x["api_series_idx"], x["game_num_in_series"])
    )

    print(
        f"\nAttempting to save {len(extracted_games_for_mapping)} game records to {output_filepath}..."
    )
    try:
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(extracted_games_for_mapping, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved game list for mapping to {output_filepath}")
        print(
            f"\nACTION: Please open this file. For each unique (round, api_series_idx) pair, identify the teams playing."
        )
        print(
            f"Then, update the 'API_SERIES_TO_DB_SERIES_MAP' in 'update_official_results.py' script."
        )
        print(
            f"For example, if (Round 1, API Index 1) shows BOS vs TOR, and your DB series for this is 'EC_R1_M1', then add (1,1): 'EC_R1_M1' to the map."
        )
    except Exception as e:
        print(f"Error saving data to JSON: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    print("--- Starting script to generate playoff game list for series mapping ---")
    fetch_game_list_for_series_mapping()
    print("\n--- Script finished ---")
