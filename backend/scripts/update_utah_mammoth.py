import sys
import os

# Add parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

from app import app, db, Team


def update_utah():
    with app.app_context():
        # Utah franchise is ID 59
        utah = Team.query.filter_by(nhl_api_id=59).first()

        if utah:
            print(f"Found team: {utah.name}. Updating to Utah Mammoth...")
            utah.name = "Utah Mammoth"
            utah.abbreviation = "UTA"
            # You might want to update the logo URL here once the official 2026 SVG is out
            # utah.logo_url = "https://assets.nhle.com/logos/nhl/svg/UTA_light.svg"
            db.session.commit()
            print("Successfully updated to Utah Mammoth (UTA).")
        else:
            print(
                "Utah franchise not found. Running full team population might be better."
            )


if __name__ == "__main__":
    update_utah()
