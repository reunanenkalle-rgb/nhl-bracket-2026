from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os


# If you installed python-dotenv and plan to use a .env file:
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Initialize CORS. This will allow requests from any origin by default.
# For development, this is often fine. For production, you might want to restrict it.
CORS(app)
# Example: To allow requests only from your Vue dev server:
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})


# --- Database Configuration ---
# Determine the absolute path for the database.
# This assumes app.py is in the 'backend' directory.
BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)  # Gets the directory where app.py is (backend/)
INSTANCE_FOLDER = os.path.join(BASE_DIR, "instance")

# Ensure the instance folder exists (optional, but good practice for clarity)
if not os.path.exists(INSTANCE_FOLDER):
    print(f"Creating instance folder at: {INSTANCE_FOLDER}")
    os.makedirs(INSTANCE_FOLDER)

DATABASE_FILE_PATH = os.path.join(INSTANCE_FOLDER, "nhl_bracket.db")

# Use an absolute path for the SQLite URI
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_FILE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

print(
    f"--- Using database at: {app.config['SQLALCHEMY_DATABASE_URI']} ---"
)  # For debugging

db = SQLAlchemy(app)  # Initialize SQLAlchemy with your app


# --- Define Your Database Models (Tables) ---
# Example: A Player model (you'll add more for brackets, teams, etc.)
class Player(db.Model):
    __tablename__ = "player"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    # Relationship to their bracket submissions
    submissions = db.relationship("BracketSubmission", backref="player", lazy=True)

    def __repr__(self):
        return f"<Player {self.name}>"


class Team(db.Model):
    __tablename__ = "team"
    id = db.Column(db.Integer, primary_key=True)  # Your auto-incrementing primary key
    nhl_api_id = db.Column(
        db.Integer, unique=True, nullable=False
    )  # NHL's unique ID (from franchise_id)
    name = db.Column(db.String(100), unique=True, nullable=False)
    abbreviation = db.Column(db.String(10), unique=True, nullable=False)  # From 'abbr'
    conference = db.Column(db.String(50), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)  # Field for the logo URL
    # common_name = db.Column(db.String(100), nullable=True) # Optional: if you want to store this too

    def __repr__(self):
        return f"<Team {self.abbreviation}>"


class Series(db.Model):
    __tablename__ = "series"
    id = db.Column(db.Integer, primary_key=True)
    round_number = db.Column(db.Integer, nullable=False)  # e.g., 1, 2, 3, 4
    series_identifier = db.Column(
        db.String(50), unique=True, nullable=False
    )  # e.g., "EC_R1_M1", "SCF"
    description = db.Column(
        db.String(100), nullable=True
    )  # e.g., "Eastern Conference Quarterfinal 1"

    # Foreign keys for the two teams in the series
    team1_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    team2_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)

    # Relationships to get Team objects
    team1 = db.relationship(
        "Team",
        foreign_keys=[team1_id],
        backref=db.backref("series_as_team1", lazy="dynamic"),
    )
    team2 = db.relationship(
        "Team",
        foreign_keys=[team2_id],
        backref=db.backref("series_as_team2", lazy="dynamic"),
    )

    # Status of the series
    status = db.Column(
        db.String(20), nullable=False, default="PENDING"
    )  # e.g., PENDING, ACTIVE, COMPLETED

    # Actual winner of the series
    actual_winner_team_id = db.Column(
        db.Integer, db.ForeignKey("team.id"), nullable=True
    )
    actual_winner = db.relationship("Team", foreign_keys=[actual_winner_team_id])

    # Optional: track games won if you want to display series scores
    games_team1_won = db.Column(db.Integer, nullable=True, default=0)
    games_team2_won = db.Column(db.Integer, nullable=True, default=0)

    # Relationship to picks made for this series
    picks_for_series = db.relationship("Pick", backref="series", lazy="dynamic")

    def __repr__(self):
        return f"<Series {self.series_identifier} (Round {self.round_number})>"


class BracketSubmission(db.Model):
    __tablename__ = "bracket_submission"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    submission_timestamp = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    bracket_name = db.Column(
        db.String(100), nullable=True
    )  # Optional name for the bracket

    # Relationship: one submission has many picks. If a submission is deleted, delete its picks.
    picks = db.relationship(
        "Pick", backref="submission", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<BracketSubmission {self.id} by Player ID {self.player_id}>"


class Pick(db.Model):
    __tablename__ = "pick"
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey("bracket_submission.id"), nullable=False
    )
    series_id = db.Column(db.Integer, db.ForeignKey("series.id"), nullable=False)
    predicted_winner_team_id = db.Column(
        db.Integer, db.ForeignKey("team.id"), nullable=False
    )

    # Relationship to easily get the predicted winner Team object
    predicted_winner = db.relationship("Team", foreign_keys=[predicted_winner_team_id])

    # You can add constraints if needed, e.g., a player can only pick one winner for a specific series in a submission
    # db.UniqueConstraint('submission_id', 'series_id', name='uq_submission_series_pick')

    def __repr__(self):
        return f"<Pick by Sub ID {self.submission_id} for Series ID {self.series_id} - Winner: Team ID {self.predicted_winner_team_id}>"


# --- API Routes ---
@app.route("/")
def home():
    return "Hello from the Flask Backend!"


@app.route("/api/test")
def test_api():
    return jsonify({"message": "API is working!", "status": "success"})


# Example: Add a new player (you'll build on this)
@app.route("/api/players", methods=["POST"])
def add_player():
    data = request.get_json()
    if not data or not "name" in data:
        return jsonify({"error": "Player name is required"}), 400

    if Player.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "Player name already exists"}), 400

    new_player = Player(name=data["name"])
    db.session.add(new_player)
    db.session.commit()
    return (
        jsonify(
            {
                "message": "Player added successfully!",
                "player": {"id": new_player.id, "name": new_player.name},
            }
        ),
        201,
    )


@app.route("/api/players", methods=["GET"])
def get_players():
    players = Player.query.all()
    return jsonify([{"id": player.id, "name": player.name} for player in players])


@app.route("/api/playoff_bracket_structure", methods=["GET"])
def get_playoff_bracket_structure():
    print(
        f"API: Attempting to query database: {app.config['SQLALCHEMY_DATABASE_URI']}"
    )  # Diagnostic
    try:
        # Ensure your models are fully defined above before this point
        series_list = Series.query.order_by(Series.round_number, Series.id).all()
        print(f"API: Found {len(series_list)} series in the database.")  # Diagnostic

        output = []
        for s in series_list:
            s_data = {
                "id": s.id,
                "round_number": s.round_number,
                "series_identifier": s.series_identifier,
                "description": s.description,
                "status": s.status,
                "team1_id": s.team1_id,
                "team1_name": s.team1.name if hasattr(s, "team1") and s.team1 else None,
                "team1_abbr": (
                    s.team1.abbreviation if hasattr(s, "team1") and s.team1 else None
                ),
                "team1_logo": (
                    s.team1.logo_url if hasattr(s, "team1") and s.team1 else None
                ),
                "team2_id": s.team2_id,
                "team2_name": s.team2.name if hasattr(s, "team2") and s.team2 else None,
                "team2_abbr": (
                    s.team2.abbreviation if hasattr(s, "team2") and s.team2 else None
                ),
                "team2_logo": (
                    s.team2.logo_url if hasattr(s, "team2") and s.team2 else None
                ),
                "actual_winner_team_id": s.actual_winner_team_id,
                "games_team1_won": s.games_team1_won,
                "games_team2_won": s.games_team2_won,
            }
            output.append(s_data)
        return jsonify(output)
    except Exception as e:
        print(f"API Error: Error querying database: {e}")  # Diagnostic
        import traceback

        traceback.print_exc()  # Print full traceback for the error
        return (
            jsonify(
                {"error": "Failed to retrieve bracket structure", "details": str(e)}
            ),
            500,
        )


@app.route("/api/bracket_submissions", methods=["POST"])
def create_bracket_submission():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    player_name = data.get("player_name")
    picks_data = data.get(
        "picks"
    )  # Expected to be list of {series_id, predicted_winner_team_id}

    if not player_name or not isinstance(picks_data, list):
        return jsonify({"error": "Missing player_name or picks"}), 400

    # --- Basic Validation: Check if all 15 series are picked ---
    # Assuming 15 series for a full bracket. Adjust if necessary.
    expected_series_count = Series.query.count()  # Or a fixed number like 15
    if len(picks_data) != expected_series_count:
        return (
            jsonify(
                {
                    "error": f"Incomplete bracket. Expected {expected_series_count} picks, got {len(picks_data)}"
                }
            ),
            400,
        )

    # Find or create player
    player = Player.query.filter_by(name=player_name).first()
    if not player:
        player = Player(name=player_name)
        db.session.add(player)
        # We might need to commit here to get player.id if it's new,
        # or structure to commit player and submission together.
        # For simplicity now, let's assume player name is unique and we handle it.
        # A better approach might be to have players register first or pass a player_id.
        try:
            db.session.commit()  # Commit to get player ID if new
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating player {player_name}: {e}")
            return jsonify({"error": "Could not create or find player"}), 500

    # Create submission
    new_submission = BracketSubmission(
        player_id=player.id,  # Use the id from the (potentially new) player object
        bracket_name=f"{player_name}'s Bracket",  # Optional: generate a name
    )
    db.session.add(new_submission)

    # It's often better to flush the session to get the new_submission.id before creating picks
    try:
        db.session.flush()  # Assigns ID to new_submission without full commit yet
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error flushing session for submission: {e}")
        return jsonify({"error": "Could not prepare submission"}), 500

    for pick_data in picks_data:
        series_id = pick_data.get("series_id")
        predicted_winner_team_id = pick_data.get("predicted_winner_team_id")

        if series_id is None or predicted_winner_team_id is None:
            db.session.rollback()  # Rollback everything if any pick is invalid
            return jsonify({"error": "Invalid pick data found"}), 400

        # Optional: Validate that series_id and predicted_winner_team_id are valid
        series_exists = Series.query.get(series_id)
        team_exists = Team.query.get(predicted_winner_team_id)
        if not series_exists or not team_exists:
            db.session.rollback()
            return (
                jsonify(
                    {
                        "error": f"Invalid series_id ({series_id}) or team_id ({predicted_winner_team_id}) in picks"
                    }
                ),
                400,
            )

        new_pick = Pick(
            submission_id=new_submission.id,  # Use the ID from the flushed submission
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
        app.logger.error(f"Error submitting bracket for player {player_name}: {e}")
        return jsonify({"error": "Failed to submit bracket"}), 500


# --- Main Execution ---
if __name__ == "__main__":
    # This is a good place to create tables if they don't exist
    # However, for more complex apps, Flask-Migrate is better for schema changes
    with app.app_context():  # Create an application context
        print("Checking and creating database tables if they don't exist...")
        db.create_all()
        print("Database tables checked/created.")

    app.run(debug=True, port=5000)
