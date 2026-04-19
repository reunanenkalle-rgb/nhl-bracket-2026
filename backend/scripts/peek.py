import requests
import json

# Let's try the carousel endpoint again, as it's the most reliable for current scores
SEASON = "20252026"
URL = f"https://api-web.nhle.com/v1/playoff-series/carousel/{SEASON}"

print(f"Peeking at: {URL}\n")

try:
    r = requests.get(URL)
    r.raise_for_status()
    data = r.json()

    # We want to find the Carolina vs Ottawa series in the data
    found = False
    for rnd in data.get("rounds", []):
        for s in rnd.get("series", []):
            top = s.get("topSeed", {}).get("abbrev")
            bottom = s.get("bottomSeed", {}).get("abbrev")

            if top == "CAR" or bottom == "CAR":
                print("--- FOUND CAROLINA SERIES ---")
                print(f"API Series Letter: {s.get('seriesLetter')}")
                print(f"Teams: {top} vs {bottom}")
                print(
                    f"Wins: {top} ({s.get('topSeed', {}).get('wins')}) - {bottom} ({s.get('bottomSeed', {}).get('wins')})"
                )
                print(f"Full JSON for this series:")
                print(json.dumps(s, indent=2))
                found = True
                break
    if not found:
        print("Could not find Carolina in the 'rounds' list. Printing top-level keys:")
        print(data.keys())

except Exception as e:
    print(f"Failed to fetch: {e}")
