# backend/scripts/inspect_playoff_boxscores.py

import json
import os
import sys
import time
import traceback  # For more detailed error printing

# Attempt to import nhlpy, provide a clear error if not found
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
PLAYOFF_GAME_TYPE_ID = 3  # Game Type ID specifically for Playoff games
MAX_GAMES_TO_INSPECT = (
    5  # <<<< Adjust this: How many game boxscores you want to fetch and save
)
OUTPUT_DIR = "fetched_data_inspection"  # Directory to save the inspection file (created in `scripts` folder)
OUTPUT_FILENAME = os.path.join(
    OUTPUT_DIR,
    f"playoff_boxscores_raw_{SEASON_TO_FETCH}_sample_first_{MAX_GAMES_TO_INSPECT}.json",
)


def fetch_and_save_sample_playoff_boxscores():
    """
    Fetches a sample of playoff game boxscores for a season and saves their raw data to a JSON file.
    """
    # Create output directory if it doesn't exist
    # This script is in backend/scripts/, so OUTPUT_DIR will be backend/scripts/fetched_data_inspection/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir_path = os.path.join(script_dir, OUTPUT_DIR)
    os.makedirs(output_dir_path, exist_ok=True)

    output_filepath = os.path.join(
        output_dir_path, os.path.basename(OUTPUT_FILENAME)
    )  # Ensure filename is just filename
    print(f"Output will be saved to: {output_filepath}")

    print("\nInitializing NHLClient...")
    try:
        client = NHLClient(
            verbose=False
        )  # Set verbose=True if you want to see nhlpy's API call logs
        print("NHLClient initialized successfully.")
    except Exception as e:
        print(f"Fatal Error: Could not initialize NHLClient: {e}")
        traceback.print_exc()
        return

    print(f"\nFetching PLAYOFF game IDs for {SEASON_TO_FETCH}...")
    playoff_game_ids_sample = []
    try:
        # Fetch all playoff game IDs for the season
        all_playoff_game_ids = client.helpers.get_gameids_by_season(
            SEASON_TO_FETCH, game_types=[PLAYOFF_GAME_TYPE_ID]
        )

        if isinstance(all_playoff_game_ids, list) and len(all_playoff_game_ids) > 0:
            # Take only the first MAX_GAMES_TO_INSPECT games for our sample
            playoff_game_ids_sample = all_playoff_game_ids[:MAX_GAMES_TO_INSPECT]
            print(
                f"  Found {len(all_playoff_game_ids)} total playoff game IDs for {SEASON_TO_FETCH}."
            )
            print(
                f"  Will fetch boxscores for the first {len(playoff_game_ids_sample)} games: {playoff_game_ids_sample}"
            )
        elif isinstance(all_playoff_game_ids, list):
            print(f"  Warning: Found 0 playoff game IDs for season {SEASON_TO_FETCH}.")
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

    if not playoff_game_ids_sample:
        print("No playoff game IDs selected to process. Exiting.")
        return

    all_fetched_boxscores = []
    processed_count = 0
    error_count = 0

    print(
        f"\nStarting to fetch raw boxscores for {len(playoff_game_ids_sample)} sampled playoff games..."
    )
    for game_id in playoff_game_ids_sample:
        processed_count += 1
        print(
            f"  Fetching boxscore for game {processed_count}/{len(playoff_game_ids_sample)} (ID: {game_id})..."
        )
        try:
            # Fetch the raw boxscore data using nhlpy
            box_score_data = client.game_center.boxscore(game_id=game_id)

            if box_score_data:  # Check if any data was returned
                # Add the source game_id to the data for easier reference later
                if isinstance(box_score_data, dict):
                    box_score_data["_fetched_for_game_id"] = game_id
                all_fetched_boxscores.append(box_score_data)
                print(f"    Successfully fetched boxscore for game ID {game_id}.")
            else:
                print(
                    f"  -> Warning: No boxscore data returned by nhlpy for game ID {game_id}."
                )
                error_count += 1

            time.sleep(0.8)  # Be polite to the API, increase if you get rate-limited
        except Exception as e:
            print(f"  -> ERROR fetching boxscore for game ID {game_id}: {e}")
            traceback.print_exc()  # Print full traceback for the error
            error_count += 1
            time.sleep(1.5)  # Longer delay after an error to be safe

    print(f"\nFinished fetching boxscores.")
    print(f"Successfully fetched: {len(all_fetched_boxscores)} boxscores.")
    if error_count > 0:
        print(f"Encountered errors for: {error_count} games.")

    if not all_fetched_boxscores:
        print("No boxscore data was successfully fetched. Nothing to save.")
        return

    print(
        f"\nAttempting to save {len(all_fetched_boxscores)} raw boxscores to {output_filepath}..."
    )
    try:
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(
                all_fetched_boxscores, f, ensure_ascii=False, indent=2
            )  # indent=2 for readability
        print(f"Successfully saved raw boxscore data to {output_filepath}")
        print(f"\nIMPORTANT: Please open and inspect this JSON file carefully.")
        print(
            f"Look for any sections related to 'playoffs', 'seriesSummary', 'seriesStatus', 'round', 'gameInSeries', or team 'wins' within a series context."
        )
    except Exception as e:
        print(f"Error saving data to JSON: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    print("--- Starting script to fetch and save sample playoff boxscores ---")
    fetch_and_save_sample_playoff_boxscores()
    print("\n--- Script finished ---")
