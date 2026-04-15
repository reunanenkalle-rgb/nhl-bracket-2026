# backend/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create the SQLAlchemy database instance here, WITHOUT the app
db = SQLAlchemy()


class Player(db.Model):
    __tablename__ = "player"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    submissions = db.relationship("BracketSubmission", backref="player", lazy=True)

    def __repr__(self):
        return f"<Player {self.name}>"


class Team(db.Model):
    __tablename__ = "team"
    id = db.Column(db.Integer, primary_key=True)
    nhl_api_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    abbreviation = db.Column(db.String(10), unique=True, nullable=False)
    conference = db.Column(db.String(50), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Team {self.abbreviation}>"


class Series(db.Model):
    __tablename__ = "series"
    id = db.Column(db.Integer, primary_key=True)
    round_number = db.Column(db.Integer, nullable=False)
    series_identifier = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=True)

    # Team IDs
    team1_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    team2_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    actual_winner_team_id = db.Column(
        db.Integer, db.ForeignKey("team.id"), nullable=True
    )

    # 2026 Specific Columns
    actual_series_length = db.Column(db.Integer, nullable=True)  # 4, 5, 6, or 7
    status = db.Column(
        db.String(20), nullable=False, default="PENDING"
    )  # PENDING, ACTIVE, COMPLETED

    # Game scores (for calculating series length)
    games_team1_won = db.Column(db.Integer, nullable=True, default=0)
    games_team2_won = db.Column(db.Integer, nullable=True, default=0)

    # Relationships (Using explicit foreign_keys to prevent mapping errors)
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
    actual_winner = db.relationship("Team", foreign_keys=[actual_winner_team_id])

    # Link to picks
    picks_for_series = db.relationship(
        "Pick", back_populates="series_rel", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Series {self.series_identifier} (Round {self.round_number})>"


class BracketSubmission(db.Model):
    __tablename__ = "bracket_submission"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    submission_timestamp = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    bracket_name = db.Column(db.String(100), nullable=True)
    picks = db.relationship(
        "Pick", backref="submission", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<BracketSubmission {self.id} by Player ID {self.player_id}>"


class Pick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey("bracket_submission.id"), nullable=False
    )
    series_id = db.Column(db.Integer, db.ForeignKey("series.id"), nullable=False)

    # 1. Ensure the ForeignKey points to 'team.id' (lowercase 't' usually)
    predicted_winner_team_id = db.Column(
        db.Integer, db.ForeignKey("team.id"), nullable=False
    )

    # 2. Add our new 2026 column
    predicted_series_length = db.Column(db.Integer, nullable=False)

    series_rel = db.relationship("Series", back_populates="picks_for_series")

    # 3. Explicitly link the relationship to the foreign key above
    predicted_winner = db.relationship("Team", foreign_keys=[predicted_winner_team_id])

    def __repr__(self):
        return f"<Pick by Sub ID {self.submission_id} for Series ID {self.series_id} - Winner: Team ID {self.predicted_winner_team_id}>"
