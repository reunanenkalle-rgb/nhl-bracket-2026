# backend/app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import traceback
from dotenv import load_dotenv
import subprocess

# Import db instance and ALL models from models.py
from models import db, Player, Team, Series, BracketSubmission, Pick, BracketPick

# Import the scoring functions
from scoring import (
    calculate_submission_stats,
    get_stanley_cup_pick_details_for_submission,
)

load_dotenv()

# --- Configuration ---
# Priority: 1. Environment Variable, 2. Default MAMMOTH2026
ACCESS_CODE = os.getenv("APP_ACCESS_CODE", "MAMMOTH2026")

app = Flask(__name__)
CORS(app)  # Crucial for Railway: Allows frontend to talk to backend

# --- Database Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# On Railway, the instance folder lives in /app/instance
INSTANCE_FOLDER = os.path.join(BASE_DIR, "instance")
if not os.path.exists(INSTANCE_FOLDER):
    os.makedirs(INSTANCE_FOLDER)

DATABASE_FILE_PATH = os.path.join(INSTANCE_FOLDER, "nhl_bracket.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_FILE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

print(f"--- DEBUG: Current Working Directory: {os.getcwd()} ---")
print(f"--- DEBUG: Loaded Access Code: '{ACCESS_CODE}' ---")
print(f"--- Using database at: {app.config['SQLALCHEMY_DATABASE_URI']} ---")

# --- API Routes ---


@app.route("/")
def home():
    return "Hello from the 2026 NHL Bracket Backend!"


@app.route("/api/test")
def test_api():
    return jsonify({"message": "API is working!", "status": "success"})


# NEW: The route that was missing to populate team lists
@app.route("/api/teams", methods=["GET"])
def get_teams():
    try:
        teams = Team.query.order_by(Team.name).all()
        return jsonify(
            [
                {
                    "id": t.id,
                    "name": t.name,
                    "abbreviation": t.abbreviation,
                    "logo_url": t.logo_url,
                }
                for t in teams
            ]
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/verify_access", methods=["POST"])
def verify_access():
    data = request.json
    user_code = data.get("code")
    print(f"--- Received code check: '{user_code}' ---")

    if user_code == ACCESS_CODE:
        return jsonify({"success": True, "message": "Access Granted"}), 200
    return jsonify({"success": False, "message": "Invalid Access Code"}), 401


@app.route("/api/playoff_bracket_structure", methods=["GET"])
def get_playoff_bracket_structure():
    try:
        series_list = Series.query.order_by(Series.round_number, Series.id).all()
        output = []
        for s in series_list:
            output.append(
                {
                    "id": s.id,
                    "round_number": s.round_number,
                    "series_identifier": s.series_identifier,
                    "description": s.description,
                    "status": s.status,
                    "team1_id": s.team1_id,
                    "team1_name": s.team1.name if s.team1 else None,
                    "team1_abbr": s.team1.abbreviation if s.team1 else None,
                    "team1_logo": s.team1.logo_url if s.team1 else None,
                    "team2_id": s.team2_id,
                    "team2_name": s.team2.name if s.team2 else None,
                    "team2_abbr": s.team2.abbreviation if s.team2 else None,
                    "team2_logo": s.team2.logo_url if s.team2 else None,
                    "actual_winner_team_id": s.actual_winner_team_id,
                    "games_team1_won": s.games_team1_won,
                    "games_team2_won": s.games_team2_won,
                }
            )

        # We return BOTH the flat list AND a wrapped version just in case
        # This fixes the "e.map is not a function" by ensuring the array is where it expects
        return jsonify(output)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return (
            jsonify([]),
            200,
        )  # Return empty list instead of error object to prevent crash


@app.route("/api/bracket_submissions", methods=["POST"])
def create_bracket_submission():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    player_name = data.get("player_name")
    picks_data = data.get("picks")

    if not player_name or not isinstance(picks_data, list):
        return jsonify({"error": "Missing player_name or picks"}), 400

    # Ensure player exists or create them
    player = Player.query.filter_by(name=player_name).first()
    if not player:
        player = Player(name=player_name)
        db.session.add(player)
        db.session.commit()

    new_submission = BracketSubmission(
        player_id=player.id, bracket_name=f"{player_name}'s Bracket"
    )
    db.session.add(new_submission)
    db.session.flush()

    for pick_data in picks_data:
        new_pick = Pick(
            submission_id=new_submission.id,
            series_id=pick_data.get("series_id"),
            predicted_winner_team_id=pick_data.get("predicted_winner_team_id"),
            predicted_series_length=pick_data.get("predicted_series_length"),
        )
        db.session.add(new_pick)

    try:
        db.session.commit()
        return (
            jsonify(
                {"message": "Bracket submitted!", "submission_id": new_submission.id}
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    try:
        submissions = BracketSubmission.query.all()
        leaderboard_data = []
        for sub in submissions:
            stats = calculate_submission_stats(sub.id)
            sc_pick = get_stanley_cup_pick_details_for_submission(sub.id)
            leaderboard_data.append(
                {
                    "submission_id": sub.id,
                    "player_name": sub.player.name if sub.player else "Unknown",
                    "score": stats["score"],
                    "percentage_correct": stats["percentage_correct"],
                    "correct_picks": stats["correct_picks_for_completed"],
                    "completed_series": stats["total_completed_series_in_playoffs"],
                    "stanley_cup_pick_abbr": (
                        sc_pick.get("team_abbr") if sc_pick else None
                    ),
                    "stanley_cup_pick_logo_url": (
                        sc_pick.get("logo_url") if sc_pick else None
                    ),
                }
            )
        leaderboard_data.sort(key=lambda x: (-x["score"], -x["percentage_correct"]))
        return jsonify(leaderboard_data)
    except Exception as e:
        return jsonify({"error": "Leaderboard error", "details": str(e)}), 500


@app.route("/api/playoff_status", methods=["GET"])
def get_playoff_status():
    # If the frontend says "undefined", it might be looking for "playoffsStarted" (camelCase)
    started = (
        Series.query.filter(
            (Series.status == "ACTIVE") | (Series.status == "COMPLETED")
        ).first()
        is not None
    )
    return jsonify(
        {
            "playoffs_started": started,
            "playoffsStarted": started,  # Adding camelCase version for frontend compatibility
        }
    )


@app.route("/api/admin/update-official-results", methods=["POST"])
def admin_update_results():
    # In a real app, you'd check a password here
    try:
        # Runs the script we just tested
        script_path = os.path.join(
            os.path.dirname(__file__), "scripts", "update_official_results.py"
        )
        result = subprocess.run(
            ["python3", script_path], capture_output=True, text=True
        )
        return jsonify(
            {"success": True, "output": result.stdout, "error": result.stderr}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/bracket_submissions/<int:submission_id>", methods=["GET"])
def get_submission_details(submission_id):
    try:
        # 1. Fetch the main submission
        submission = BracketSubmission.query.get_or_404(submission_id)

        # 2. Fetch all picks
        picks = BracketPick.query.filter_by(submission_id=submission_id).all()

        picks_data = []
        for p in picks:
            s = p.series  # Get the associated series for this pick
            picks_data.append(
                {
                    "series_id": p.series_id,
                    "series_identifier": s.series_identifier,
                    "round_number": s.round_number,
                    "predicted_winner_team_id": p.predicted_winner_team_id,
                    "predicted_series_length": p.predicted_series_length,
                    # Include team info so the read-only view knows who played
                    "team1": {
                        "name": s.team1.name if s.team1 else "TBD",
                        "abbreviation": s.team1.abbreviation if s.team1 else "TBD",
                        "logo_url": s.team1.logo_url if s.team1 else None,
                    },
                    "team2": {
                        "name": s.team2.name if s.team2 else "TBD",
                        "abbreviation": s.team2.abbreviation if s.team2 else "TBD",
                        "logo_url": s.team2.logo_url if s.team2 else None,
                    },
                    # Official results for highlighting correct/incorrect picks
                    "actual_winner_team_id": s.actual_winner_team_id,
                    "status": s.status,
                }
            )

        return jsonify(
            {
                "id": submission.id,
                "player_name": submission.player_name,
                "score": submission.total_score,  # Frontend expects 'score', not 'total_score'
                "correct_picks_count": 0,  # You can add logic to calculate this later
                "percentage_correct": 0,
                "picks": picks_data,
            }
        )
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500


# --- Main Execution ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # Railway uses Gunicorn in production, but for local dev:
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
