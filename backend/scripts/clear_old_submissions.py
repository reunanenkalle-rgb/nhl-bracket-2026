# backend/scripts/clear_old_submissions.py
import sys
import os

# Add parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from app import app
from models import db, BracketSubmission, Pick


def clear_2025_data():
    with app.app_context():
        print("--- Cleaning up 2025 Bracket Data ---")
        try:
            # 1. Delete all individual picks
            num_picks = Pick.query.delete()
            print(f"Deleted {num_picks} picks from 2025.")

            # 2. Delete all bracket submissions
            num_subs = BracketSubmission.query.delete()
            print(f"Deleted {num_subs} bracket submissions from 2025.")

            # Note: We keep the Player table so your friends
            # don't have to re-create their names if they use the same ones.

            db.session.commit()
            print("\nDatabase is now fresh and ready for 2026 picks!")
        except Exception as e:
            db.session.rollback()
            print(f"Error during cleanup: {e}")


if __name__ == "__main__":
    clear_2025_data()
