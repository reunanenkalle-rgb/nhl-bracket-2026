# backend/app.py

from flask import Flask, jsonify, request
from flask_cors import CORS

# Removed: from flask_sqlalchemy import SQLAlchemy (db comes from models.py)
# Removed: from datetime import datetime (now in models.py)
import os
import traceback

# Import db instance and ALL models from models.py
from models import db, Player, Team, Series, BracketSubmission, Pick

# Import the scoring function
from scoring import (
    calculate_submission_stats,
    get_stanley_cup_pick_details_for_submission,
)

# Create Flask app

app = Flask(__name__)  # Create Flask app instance
CORS(app)

# --- Database Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_FOLDER = os.path.join(BASE_DIR, "instance")
if not os.path.exists(INSTANCE_FOLDER):
    os.makedirs(INSTANCE_FOLDER)
DATABASE_FILE_PATH = os.path.join(INSTANCE_FOLDER, "nhl_bracket.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_FILE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["LOGGING_LEVEL"] = "DEBUG"  # For app.logger messages

print(f"--- Using database at: {app.config['SQLALCHEMY_DATABASE_URI']} ---")

db.init_app(app)  # Initialize the db instance from models.py with the app

# --- API Routes ---
# (Your existing routes: /, /api/test, /api/playoff_bracket_structure, /api/official_results)
# Ensure they use models imported from `models` (e.g., Series.query...)


@app.route("/")
def home():
    return "Hello from the Flask Backend for NHL Bracket App!"


@app.route("/api/test")
def test_api():
    return jsonify({"message": "API is working!", "status": "success"})


@app.route("/api/playoff_bracket_structure", methods=["GET"])
def get_playoff_bracket_structure():
    # ... (your existing logic, Series.query will use Series from models.py) ...
    # (Make sure this function is complete as per previous versions)
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
    return jsonify(output)


@app.route("/api/official_results", methods=["GET"])
def get_official_results():
    # ... (your existing logic, Series.query will use Series from models.py) ...
    # (Make sure this function is complete)
    series_list = Series.query.order_by(Series.round_number, Series.id).all()
    output = []
    for (
        s
    ) in series_list:  # Copied from thought process Turn 42, ensure it's what you have
        output.append(
            {
                "id": s.id,
                "series_identifier": s.series_identifier,
                "round_number": s.round_number,
                "description": s.description,
                "status": s.status,
                "team1_id": s.team1_id,
                "team1_name": s.team1.name if s.team1 else None,
                "team1_abbr": s.team1.abbreviation if s.team1 else None,
                "team1_logo": s.team1.logo_url if s.team1 else None,
                "games_team1_won": s.games_team1_won,
                "team2_id": s.team2_id,
                "team2_name": s.team2.name if s.team2 else None,
                "team2_abbr": s.team2.abbreviation if s.team2 else None,
                "team2_logo": s.team2.logo_url if s.team2 else None,
                "games_team2_won": s.games_team2_won,
                "actual_winner_team_id": s.actual_winner_team_id,
            }
        )
    return jsonify(output)


@app.route("/api/bracket_submissions", methods=["POST"])
def create_bracket_submission():
    # ... (your existing logic, ensure Player, Series, Team, BracketSubmission, Pick are from models.py) ...
    # (Make sure this function is complete and uses imported models)
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    player_name = data.get("player_name")
    picks_data = data.get("picks")
    if not player_name or not isinstance(picks_data, list):
        return jsonify({"error": "Missing player_name or picks"}), 400
    expected_series_count = Series.query.count()
    if len(picks_data) != expected_series_count:
        return (
            jsonify(
                {
                    "error": f"Incomplete bracket. Expected {expected_series_count} picks, got {len(picks_data)}"
                }
            ),
            400,
        )
    player = Player.query.filter_by(name=player_name).first()
    if not player:
        player = Player(name=player_name)
        db.session.add(player)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating player {player_name}: {e}")
            return jsonify({"error": "Could not create or find player"}), 500
    new_submission = BracketSubmission(
        player_id=player.id, bracket_name=f"{player_name}'s Bracket"
    )
    db.session.add(new_submission)
    try:
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error flushing submission: {e}")
        return jsonify({"error": "Could not prepare submission"}), 500
    for pick_data in picks_data:
        series_id = pick_data.get("series_id")
        predicted_winner_team_id = pick_data.get("predicted_winner_team_id")
        if series_id is None or predicted_winner_team_id is None:
            db.session.rollback()
            return jsonify({"error": "Invalid pick data"}), 400
        if not Series.query.get(series_id) or not Team.query.get(
            predicted_winner_team_id
        ):
            db.session.rollback()
            return jsonify({"error": "Invalid series/team ID in pick"}), 400
        new_pick = Pick(
            submission_id=new_submission.id,
            series_id=series_id,
            predicted_winner_team_id=predicted_winner_team_id,
        )
        db.session.add(new_pick)
    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Bracket submitted successfully!",
                    "submission_id": new_submission.id,
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error submitting bracket for {player_name}: {e}")
        return jsonify({"error": "Failed to submit bracket"}), 500


@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    try:
        submissions = (
            BracketSubmission.query.all()
        )  # Or filter for active/valid submissions
        leaderboard_data = []

        # Pre-fetch all series once to calculate total_completed_series_in_playoffs efficiently
        # This count is now done within calculate_submission_stats, which is fine for moderate numbers of submissions.
        # If performance becomes an issue with many submissions, total_completed_series_in_playoffs
        # could be calculated once here and passed to an adapted calculate_submission_stats.

        for sub in submissions:
            stats = calculate_submission_stats(
                sub.id
            )  # Gets score, correct_picks, total_completed, percentage
            sc_pick_details = get_stanley_cup_pick_details_for_submission(sub.id)

            player_name = sub.player.name if sub.player else "Unknown Player"

            leaderboard_data.append(
                {
                    "submission_id": sub.id,
                    "player_name": player_name,
                    "score": stats["score"],
                    "percentage_correct": stats["percentage_correct"],  # e.g., 75.0
                    "correct_picks": stats["correct_picks_for_completed"],  # e.g., 6
                    "completed_series": stats[
                        "total_completed_series_in_playoffs"
                    ],  # e.g., 8
                    "stanley_cup_pick_abbr": (
                        sc_pick_details.get("team_abbr") if sc_pick_details else None
                    ),
                    "stanley_cup_pick_logo_url": (
                        sc_pick_details.get("logo_url") if sc_pick_details else None
                    ),
                }
            )

        # Sort by score descending, then by percentage correct descending, then by player name ascending
        leaderboard_data.sort(
            key=lambda x: (-x["score"], -x["percentage_correct"], x["player_name"])
        )

        return jsonify(leaderboard_data)
    except Exception as e:
        app.logger.error(f"Error generating leaderboard: {e}")
        traceback.print_exc()
        return (
            jsonify({"error": "Could not generate leaderboard", "details": str(e)}),
            500,
        )


# Your other routes (get_submission_details, etc.) would also use calculate_submission_stats
# if they need to display the score and percentage for an individual bracket.
# For example, in get_submission_details:
#   stats = calculate_submission_stats(submission_id)
#   return jsonify({ ..., "score": stats["score"], "percentage_correct": stats["percentage_correct"], ...})


@app.route("/api/bracket_submissions/<int:submission_id>", methods=["GET"])
def get_submission_details(submission_id):
    # ... (your existing logic using calculate_submission_score and models from models.py) ...
    # (Make sure this function is complete and uses imported models)
    try:
        submission = BracketSubmission.query.get_or_404(submission_id)
        # ... (rest of your function as per Turn 44, ensuring models are used correctly) ...
        player_name = submission.player.name if submission.player else "Unknown Player"  # type: ignore
        stats = calculate_submission_stats(submission_id)
        picks_details = []
        for pick in submission.picks:
            series = Series.query.get(pick.series_id)
            if not series:
                continue
            predicted_winner = (
                Team.query.get(pick.predicted_winner_team_id)
                if pick.predicted_winner_team_id
                else None
            )
            actual_winner = (
                Team.query.get(series.actual_winner_team_id)
                if series.actual_winner_team_id
                else None
            )
            series_team1 = series.team1
            series_team2 = series.team2
            picks_details.append(
                {
                    "series_id": series.id,
                    "series_identifier": series.series_identifier,
                    "description": series.description,
                    "round_number": series.round_number,
                    "series_team1_abbr": (
                        series_team1.abbreviation if series_team1 else "TBD"
                    ),
                    "series_team1_logo": (
                        series_team1.logo_url if series_team1 else None
                    ),
                    "series_team2_abbr": (
                        series_team2.abbreviation if series_team2 else "TBD"
                    ),
                    "series_team2_logo": (
                        series_team2.logo_url if series_team2 else None
                    ),
                    "predicted_winner_team_id": pick.predicted_winner_team_id,
                    "predicted_winner_abbr": (
                        predicted_winner.abbreviation if predicted_winner else None
                    ),
                    "predicted_winner_logo": (
                        predicted_winner.logo_url if predicted_winner else None
                    ),
                    "actual_winner_team_id": series.actual_winner_team_id,
                    "actual_winner_abbr": (
                        actual_winner.abbreviation if actual_winner else None
                    ),
                    "actual_winner_logo": (
                        actual_winner.logo_url if actual_winner else None
                    ),
                    "games_team1_won": series.games_team1_won,
                    "games_team2_won": series.games_team2_won,
                    "series_status": series.status,
                    "is_pick_correct": (
                        True
                        if series.status == "COMPLETED"
                        and pick.predicted_winner_team_id
                        == series.actual_winner_team_id
                        else (False if series.status == "COMPLETED" else None)
                    ),
                }
            )
        picks_details.sort(key=lambda p: (p["round_number"], p["series_identifier"]))
        return jsonify(
            {
                "submission_id": submission.id,
                "player_name": player_name,
                "bracket_name": submission.bracket_name,
                "submission_timestamp": (
                    submission.submission_timestamp.isoformat()
                    if submission.submission_timestamp
                    else None
                ),
                # Unpack the stats here:
                "score": stats["score"],
                "percentage_correct": stats["percentage_correct"],
                "correct_picks_count": stats[
                    "correct_picks_for_completed"
                ],  # Use consistent key from stats dict
                "total_completed_series_count": stats[
                    "total_completed_series_in_playoffs"
                ],  # Use consistent key
                "picks": picks_details,
            }
        )

    except Exception as e:
        app.logger.error(
            f"Error fetching submission details for ID {submission_id}: {e}"
        )
        traceback.print_exc()
        return (
            jsonify(
                {"error": "Could not retrieve submission details", "details": str(e)}
            ),
            500,
        )


@app.route("/api/playoff_status", methods=["GET"])
def get_playoff_status():
    try:
        # Check if any series has recorded games won by either team
        # or if any series is marked as ACTIVE or COMPLETED
        active_or_completed_series = Series.query.filter(
            (Series.games_team1_won > 0)
            | (Series.games_team2_won > 0)
            | (Series.status == "ACTIVE")
            | (Series.status == "COMPLETED")
        ).first()  # .first() is efficient, we only need to know if at least one exists

        playoffs_have_started = active_or_completed_series is not None

        # You might also want to add a manual override or a specific "lock date" from config
        # For now, this data-driven check is good.

        return jsonify({"playoffs_started": playoffs_have_started})
    except Exception as e:
        app.logger.error(f"Error fetching playoff status: {e}")
        traceback.print_exc()
        return (
            jsonify({"error": "Could not determine playoff status", "details": str(e)}),
            500,
        )


@app.route("/api/bracket_submissions_list", methods=["GET"])
def get_all_submissions_list():
    # ... (your existing logic using calculate_submission_score and models from models.py) ...
    # (Make sure this function is complete and uses imported models)
    try:
        submissions = BracketSubmission.query.order_by(
            BracketSubmission.submission_timestamp.desc()
        ).all()
        output = []
        for sub in submissions:
            output.append(
                {
                    "submission_id": sub.id,
                    "player_name": sub.player.name if sub.player else "Unknown",
                    "bracket_name": sub.bracket_name,
                    "submitted_at": (
                        sub.submission_timestamp.isoformat()
                        if sub.submission_timestamp
                        else None
                    ),
                    "score": calculate_submission_stats(sub.id),
                }
            )
        return jsonify(output)
    except Exception as e:
        app.logger.error(f"Error listing submissions: {e}")
        traceback.print_exc()
        return jsonify({"error": "Could not list submissions"}), 500


# --- Main Execution / Create Tables ---
if __name__ == "__main__":
    with app.app_context():  # Important: create_all needs an app context
        print(
            "Checking and creating database tables if they don't exist (from app.py)..."
        )
        db.create_all()  # This will now use the models defined in models.py
        print("Database tables checked/created (from app.py).")
    app.run(debug=True, port=5000)
