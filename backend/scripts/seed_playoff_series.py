import sys
import os
import json

# Add parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from app import app
from models import db, Series, Team


def seed_playoff_series():
    # Path to the 2026 JSON in the same scripts folder
    json_path = os.path.join(current_dir, "initial_bracket_2026.json")

    if not os.path.exists(json_path):
        print(f"CRITICAL ERROR: {json_path} not found.")
        return

    with open(json_path, "r") as f:
        bracket_data = json.load(f)

    with app.app_context():
        print("--- CLEANING DATABASE FOR 2026 SEASON ---")
        # Note: In a production app, we would move 2025 to an archive.
        # For this setup, we clear the table to start fresh.
        try:
            db.session.query(Series).delete()
            db.session.commit()
            print("Database cleared successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Cleanup error: {e}")
            return

        print(f"--- SEEDING ROUND 1 MATCHUPS ({bracket_data['season']}) ---")

        # 1. Seed Round 1 (The only round where teams are already known)
        for round_info in bracket_data["rounds"]:
            if round_info["round_number"] == 1:
                for series_data in round_info["series"]:
                    t1 = Team.query.filter_by(
                        abbreviation=series_data["team1_abbr"]
                    ).first()
                    t2 = Team.query.filter_by(
                        abbreviation=series_data["team2_abbr"]
                    ).first()

                    if not t1 or not t2:
                        print(
                            f"Warning: Team not found for {series_data['series_identifier']}"
                        )

                    series = Series(
                        round_number=1,
                        series_identifier=series_data["series_identifier"],
                        description=series_data["description"],
                        team1_id=t1.id if t1 else None,
                        team2_id=t2.id if t2 else None,
                        status="PENDING",
                    )
                    db.session.add(series)

        db.session.commit()  # Commit R1 so we can link them to R2

        # 2. Seed Future Rounds (R2, R3, R4) with Parent Links
        # We define which R1 series "feed" into which R2 series
        print("--- CREATING BRACKET TREE LOGIC (R2-R4) ---")

        # Helpers to find series by their ID string
        def get_series_id(ident):
            s = Series.query.filter_by(series_identifier=ident).first()
            return s.id if s else None

        future_rounds = [
            # Round 2: Conference Semifinals
            {
                "round": 2,
                "id": "EC_R2_M1",
                "parent1": "EC_R1_M1",
                "parent2": "EC_R1_M2",
                "desc": "Eastern Conf Semifinal 1",
            },
            {
                "round": 2,
                "id": "EC_R2_M2",
                "parent1": "EC_R1_M3",
                "parent2": "EC_R1_M4",
                "desc": "Eastern Conf Semifinal 2",
            },
            {
                "round": 2,
                "id": "WC_R2_M1",
                "parent1": "WC_R1_M1",
                "parent2": "WC_R1_M2",
                "desc": "Western Conf Semifinal 1",
            },
            {
                "round": 2,
                "id": "WC_R2_M2",
                "parent1": "WC_R1_M3",
                "parent2": "WC_R1_M4",
                "desc": "Western Conf Semifinal 2",
            },
            # Round 3: Conference Finals
            {
                "round": 3,
                "id": "EC_R3_CF",
                "parent1": "EC_R2_M1",
                "parent2": "EC_R2_M2",
                "desc": "Eastern Conference Final",
            },
            {
                "round": 3,
                "id": "WC_R3_CF",
                "parent1": "WC_R2_M1",
                "parent2": "WC_R2_M2",
                "desc": "Western Conference Final",
            },
            # Round 4: Stanley Cup Final
            {
                "round": 4,
                "id": "SCF",
                "parent1": "EC_R3_CF",
                "parent2": "WC_R3_CF",
                "desc": "Stanley Cup Final",
            },
        ]

        for fr in future_rounds:
            new_series = Series(
                round_number=fr["round"],
                series_identifier=fr["id"],
                description=fr["desc"],
                status="PENDING",
                # If your model has team1_from_series_id, add it here:
                # team1_from_series_id=get_series_id(fr["parent1"]),
                # team2_from_series_id=get_series_id(fr["parent2"])
            )
            db.session.add(new_series)

        db.session.commit()
        print("--- 2026 BRACKET SEEDING COMPLETE ---")


if __name__ == "__main__":
    seed_playoff_series()
