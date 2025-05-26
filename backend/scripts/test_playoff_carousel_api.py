# backend/scripts/test_playoff_carousel_api.py

import requests
import json
import os
import sys

# --- Configuration ---
# Using 20232024 as it's a completed playoff season and should provide full data examples.
# You can change this to 20242025 to see current/recent playoff data.
SEASON_TO_TEST = "20242025"
API_BASE_URL = "https://api-web.nhle.com"
ENDPOINT_PATH = f"/v1/playoff-series/carousel/{SEASON_TO_TEST}/"
FULL_API_URL = f"{API_BASE_URL}{ENDPOINT_PATH}"

# Output file for inspection (optional, but helpful)
OUTPUT_DIR = "fetched_data_inspection"
OUTPUT_FILENAME = os.path.join(
    OUTPUT_DIR, f"playoff_carousel_response_{SEASON_TO_TEST}.json"
)


def fetch_playoff_carousel_data():
    """
    Fetches data from the NHL playoff series carousel API for the specified season
    and prints it. Optionally saves to a file.
    """
    print(f"Attempting to fetch data from: {FULL_API_URL}")

    try:
        response = requests.get(FULL_API_URL, timeout=10)  # Added a timeout
        response.raise_for_status()  # This will raise an HTTPError for bad responses (4XX or 5XX)

        print(f"\nRequest successful! Status Code: {response.status_code}")

        # Parse the JSON response
        data = response.json()

        # Pretty print the JSON data to the console
        print("\n--- API Response Data (Formatted JSON) ---")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("--- End of API Response Data ---")

        # Optionally save to a file for easier inspection
        save_to_file = True  # Set to False if you don't want to save
        if save_to_file:
            # Create output directory if it doesn't exist
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir_path = os.path.join(script_dir, OUTPUT_DIR)
            os.makedirs(output_dir_path, exist_ok=True)
            output_filepath = os.path.join(
                output_dir_path, os.path.basename(OUTPUT_FILENAME)
            )

            try:
                with open(output_filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\nSuccessfully saved full API response to: {output_filepath}")
            except IOError as e:
                print(f"\nError saving data to file {output_filepath}: {e}")

        return data

    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTP error occurred: {http_err}")
        print(f"Response Content: {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"\nConnection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"\nRequest timed out: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"\nAn error occurred with the request: {req_err}")
    except json.JSONDecodeError:
        print("\nError: Could not decode JSON from the response.")
        print(f"Response Content: {response.text}")

    return None


if __name__ == "__main__":
    print(
        f"--- Testing NHL Playoff Series Carousel API for season {SEASON_TO_TEST} ---"
    )
    fetched_data = fetch_playoff_carousel_data()

    if fetched_data:
        # After printing, you can add specific checks here based on what you expect
        # For example, if 'series' is a key in the root object:
        if "series" in fetched_data and isinstance(fetched_data["series"], list):
            print(
                f"\nFound {len(fetched_data['series'])} series entries in the response."
            )
            if fetched_data["series"]:
                print("Example of the first series entry:")
                print(
                    json.dumps(fetched_data["series"][0], indent=2, ensure_ascii=False)
                )
        else:
            print(
                "\nCould not find a 'series' list in the root of the response, or it's not a list."
            )
            print("Please inspect the full output above to understand the structure.")

    print("\n--- Test script finished ---")
