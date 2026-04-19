import requests
import json

SEASON = "20252026"
# This matches the endpoint in your current script
URL = f"https://api-web.nhle.com/v1/playoff-bracket/{SEASON}"

print(f"--- FETCHING DATA FROM: {URL} ---\n")

try:
    response = requests.get(URL, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "rounds" in data and len(data["rounds"]) > 0:
        first_round = data["rounds"][0]
        print(f"FOUND ROUND: {first_round.get('roundNumber')}")

        if "series" in first_round and len(first_round["series"]) > 0:
            s = first_round["series"][0]
            print("\n--- SAMPLE SERIES DATA STRUCTURE ---")
            print(json.dumps(s, indent=2))

            # Specific Checks for your script
            print("\n--- SCRIPT COMPATIBILITY CHECK ---")
            print(
                f"Has 'seriesLetter'?: {'seriesLetter' in s} (Value: {s.get('seriesLetter')})"
            )
            print(f"Has 'topSeed'?: {'topSeed' in s}")
            if "topSeed" in s:
                print(f"  - Top Seed Abbr: {s['topSeed'].get('abbrev')}")
                print(f"  - Top Seed Wins: {s['topSeed'].get('wins')}")
            print(f"Has 'bottomSeed'?: {'bottomSeed' in s}")

    else:
        print("❌ ERROR: No 'rounds' found in response.")
        print("Full API Response Keys:", data.keys())

except Exception as e:
    print(f"❌ API REQUEST FAILED: {e}")
