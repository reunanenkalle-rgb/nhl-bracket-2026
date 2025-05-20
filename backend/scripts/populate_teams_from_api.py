# backend/scripts/populate_teams_from_api.py

import sys
import os

# This makes sure the script can find the 'app' module in the parent 'backend' directory
# Adjust if your script is in the same directory as app.py
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from nhlpy import NHLClient  # Your NHL API library

    # Assuming your Flask app object is named 'app' and SQLAlchemy instance is 'db'
    # and your Team model is defined in 'app.py' located in the parent directory.
    from app import app, db, Team  # And any other models you might eventually need here
except ImportError as e:
    print(f"Error importing necessary modules. Please check your setup and PYTHONPATH.")
    print(f"Details: {e}")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)


def fetch_and_populate_teams():
    """
    Fetches team data from the NHL API and populates/updates the Team table in the database.
    """
    print("Initializing NHLClient...")
    try:
        client = NHLClient(verbose=False)
        print("NHLClient initialized successfully.")
    except Exception as e:
        print(f"Fatal Error: Could not initialize NHLClient: {e}")
        return

    print("Attempting to fetch teams information from API...")
    api_teams_data = None
    try:
        api_teams_data = client.teams.teams_info()

        if isinstance(api_teams_data, list) and len(api_teams_data) > 0:
            print(
                f"Successfully fetched data for {len(api_teams_data)} teams from API."
            )
        elif isinstance(api_teams_data, list) and len(api_teams_data) == 0:
            print("Warning: API returned an empty list of teams. No data to process.")
            return
        else:
            print(
                f"Warning: Expected a list of teams, but received type: {type(api_teams_data)}. Cannot process."
            )
            return
    except Exception as e:
        print(f"Error: Failed to fetch teams information from the API: {e}")
        return

    # This must be done within the Flask application context to interact with the database
    with app.app_context():
        # --- Ensure all tables are created based on defined models ---
        # This is safe to call multiple times; it won't recreate existing tables or
        # alter them if they already match the models.
        print("Ensuring database tables are created (if they don't exist)...")
        db.create_all()
        print("Database tables checked/created.")
        # --- End of table creation ---

        print("\nProcessing and populating teams into the database...")
        teams_added_count = 0
        teams_updated_count = 0
        teams_skipped_count = 0

        for team_data_from_api in api_teams_data:
            if not isinstance(team_data_from_api, dict):
                print(f"Skipping item as it's not a dictionary: {team_data_from_api}")
                teams_skipped_count += 1
                continue

            try:
                nhl_id_val = team_data_from_api.get("franchise_id")
                if nhl_id_val is None:
                    print(
                        f"Skipping team due to missing 'franchise_id'. Data: {team_data_from_api}"
                    )
                    teams_skipped_count += 1
                    continue
                nhl_id = int(nhl_id_val)

                name = team_data_from_api.get("name")
                abbreviation = team_data_from_api.get("abbr")
                logo_url = team_data_from_api.get("logo")

                conference_data = team_data_from_api.get("conference")
                conference_name = (
                    conference_data.get("name")
                    if isinstance(conference_data, dict)
                    else None
                )

                if not name or not abbreviation:
                    print(
                        f"Skipping team (NHL ID: {nhl_id}) due to missing 'name' or 'abbr'. Data: {team_data_from_api}"
                    )
                    teams_skipped_count += 1
                    continue

            except ValueError as e:
                print(
                    f"Skipping team due to 'franchise_id' conversion error: {e}. Franchise ID was: '{nhl_id_val}'. Data: {team_data_from_api}"
                )
                teams_skipped_count += 1
                continue
            except Exception as e:
                print(
                    f"Skipping team due to an unexpected parsing error: {e}. Data: {team_data_from_api}"
                )
                teams_skipped_count += 1
                continue

            existing_team = Team.query.filter_by(nhl_api_id=nhl_id).first()

            if existing_team:
                updated_fields = []
                if existing_team.name != name:
                    existing_team.name = name
                    updated_fields.append("name")
                if existing_team.abbreviation != abbreviation:
                    existing_team.abbreviation = abbreviation
                    updated_fields.append("abbreviation")
                if existing_team.logo_url != logo_url:
                    existing_team.logo_url = logo_url
                    updated_fields.append("logo_url")
                if (
                    conference_name is not None
                    and existing_team.conference != conference_name
                ):
                    existing_team.conference = conference_name
                    updated_fields.append("conference")
                elif conference_name is None and existing_team.conference is not None:
                    existing_team.conference = None
                    updated_fields.append("conference (set to None)")

                if updated_fields:
                    print(
                        f"Updating team: {name} (NHL API ID: {nhl_id}). Changed: {', '.join(updated_fields)}"
                    )
                    teams_updated_count += 1
            else:
                print(f"Adding new team: {name} (NHL API ID: {nhl_id})")
                new_team = Team(
                    nhl_api_id=nhl_id,
                    name=name,
                    abbreviation=abbreviation,
                    conference=conference_name,
                    logo_url=logo_url,
                )
                db.session.add(new_team)
                teams_added_count += 1

        try:
            db.session.commit()
            print(f"\nDatabase commit successful.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing to database: {e}")
        finally:
            print(
                f"Process summary: Teams added: {teams_added_count}, Teams updated: {teams_updated_count}, Teams skipped: {teams_skipped_count}"
            )


if __name__ == "__main__":
    print("Starting team population script...")
    fetch_and_populate_teams()
    print("\nTeam population script finished.")
