from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


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
# In a real app, you'd get this from your .env file
# For SQLite, it's the path to your database file.
# It will be created in your 'backend' directory if it doesn't exist.
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nhl_bracket.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Suppresses a warning

db = SQLAlchemy(app)  # Initialize SQLAlchemy with your app


# --- Define Your Database Models (Tables) ---
# Example: A Player model (you'll add more for brackets, teams, etc.)
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    # Relationship to their bracket submissions
    submissions = db.relationship("BracketSubmission", backref="player", lazy=True)

    def __repr__(self):
        return f"<Player {self.name}>"


class Team(db.Model):
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


class BracketSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bracket_name = db.Column(db.String(100), nullable=False, default="My Bracket")
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    # timestamp_submitted = db.Column(db.DateTime, default=datetime.utcnow) # Requires import datetime

    # Relationship to individual picks in this submission
    picks = db.relationship(
        "Pick", backref="submission", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<BracketSubmission {self.id} by Player {self.player_id}>"


class Pick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey("bracket_submission.id"), nullable=False
    )
    series_identifier = db.Column(
        db.String(50), nullable=False
    )  # e.g., "R1M1_EC", "SCF"
    predicted_winner_team_id = db.Column(
        db.Integer, db.ForeignKey("team.id"), nullable=False
    )

    # predicted_winner = db.relationship('Team') # To easily access team info from a pick

    def __repr__(self):
        return f"<Pick for Series {self.series_identifier} in Sub {self.submission_id}>"


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


# --- Main Execution ---
if __name__ == "__main__":
    # This is a good place to create tables if they don't exist
    # However, for more complex apps, Flask-Migrate is better for schema changes
    with app.app_context():  # Create an application context
        db.create_all()  # Creates tables based on your models

    app.run(debug=True, port=5000)
