# backend/scripts/seed_playoff_series.py

import sys
import os
import json
from app import app  # Still need 'app' from app.py for its config and app_context
from models import db, Team, Series  # Import db and models from models.py

# This makes sure the script can find the 'app' module in the parent 'backend' directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    # Assuming your Flask app object is named 'app', SQLAlchemy instance is 'db',
    # and your models (Team, Series) are defined in 'app.py' located in the parent directory.
    from app import app, db, Team, Series
except ImportError as e:
    print(f"Error importing necessary modules. Please check your setup and PYTHONPATH.")
    print(f"Details: {e}")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

# Define the path to your JSON file
JSON_FILE_PATH = os.path.join(current_dir, "initial_bracket_2025.json")


def seed_series_data():
    """
    Reads the initial_bracket_2025.json file and populates the Series table.
    """
    print(f"Attempting to load series definitions from: {JSON_FILE_PATH}")
    try:
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(
            f"Successfully loaded series definitions for playoff year: {data.get('playoff_year')}"
        )
    except FileNotFoundError:
        print(f"Error: JSON file not found at {JSON_FILE_PATH}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from {JSON_FILE_PATH}. Details: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading the JSON file: {e}")
        return

    series_definitions = data.get("series_definitions")
    if not isinstance(series_definitions, list):
        print(
            "Error: 'series_definitions' key not found or is not a list in the JSON file."
        )
        return

    # Use the Flask application context to interact with the database
    with app.app_context():
        # Ensure all tables are created (idempotent - won't recreate if they exist)
        print("Ensuring database tables are created (if they don't exist)...")
        db.create_all()  # Make sure Team, Series, etc. models are defined and imported
        print("Database tables checked/created.")

        print("\nProcessing and seeding series into the database...")
        series_added_count = 0
        series_skipped_count = 0
        series_errors_count = 0

        for series_def in series_definitions:
            series_identifier = series_def.get("series_identifier")
            round_number = series_def.get("round_number")
            description = series_def.get("description")

            if not all([series_identifier, round_number, description]):
                print(
                    f"Skipping series due to missing identifier, round, or description: {series_def}"
                )
                series_errors_count += 1
                continue

            # Check if the series already exists to avoid duplicates
            existing_series = Series.query.filter_by(
                series_identifier=series_identifier
            ).first()
            if existing_series:
                print(
                    f"Series '{series_identifier}' already exists in the database. Skipping."
                )
                series_skipped_count += 1
                continue

            team1_id = None
            team2_id = None

            # For Round 1, try to find team IDs based on abbreviations
            if round_number == 1:
                team1_abbr = series_def.get("team1_abbr")
                team2_abbr = series_def.get("team2_abbr")

                if team1_abbr:
                    team1_obj = Team.query.filter_by(abbreviation=team1_abbr).first()
                    if team1_obj:
                        team1_id = team1_obj.id
                    else:
                        print(
                            f"Warning: Team with abbreviation '{team1_abbr}' not found for series '{series_identifier}'. Team 1 will be NULL."
                        )

                if team2_abbr:
                    team2_obj = Team.query.filter_by(abbreviation=team2_abbr).first()
                    if team2_obj:
                        team2_id = team2_obj.id
                    else:
                        print(
                            f"Warning: Team with abbreviation '{team2_abbr}' not found for series '{series_identifier}'. Team 2 will be NULL."
                        )

                if not team1_id or not team2_id:
                    print(
                        f"Warning: One or both teams for Round 1 series '{series_identifier}' could not be found by abbreviation. Proceeding with NULL team IDs where applicable."
                    )

            # Create the new Series object
            try:
                new_series = Series(
                    round_number=round_number,
                    series_identifier=series_identifier,
                    description=description,
                    team1_id=team1_id,  # Will be None if not found or not Round 1
                    team2_id=team2_id,  # Will be None if not found or not Round 1
                    status="PENDING",  # Default status
                )
                db.session.add(new_series)
                series_added_count += 1
                print(
                    f"Prepared to add series: '{series_identifier}' (Round {round_number})"
                )
            except Exception as e:
                print(f"Error creating Series object for '{series_identifier}': {e}")
                series_errors_count += 1
                continue

        # Commit all new series to the database
        try:
            db.session.commit()
            print(f"\nDatabase commit successful for series data.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing series data to database: {e}")
        finally:
            print(
                f"Series seeding summary: Added: {series_added_count}, Skipped (already existed): {series_skipped_count}, Errors: {series_errors_count}"
            )


if __name__ == "__main__":
    print("Starting playoff series seeding script...")
    seed_series_data()
    print("\nPlayoff series seeding script finished.")
