# backend/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Player(db.Model):
    __tablename__ = "player"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    submissions = db.relationship("BracketSubmission", backref="player", lazy=True)


class Team(db.Model):
    __tablename__ = "team"
    id = db.Column(db.Integer, primary_key=True)
    nhl_api_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    abbreviation = db.Column(db.String(10), unique=True, nullable=False)
    conference = db.Column(db.String(50), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)


class Series(db.Model):
    __tablename__ = "series"
    id = db.Column(db.Integer, primary_key=True)
    round_number = db.Column(db.Integer, nullable=False)
    series_identifier = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=True)
    team1_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    team2_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    actual_winner_team_id = db.Column(
        db.Integer, db.ForeignKey("team.id"), nullable=True
    )
    actual_series_length = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="PENDING")
    games_team1_won = db.Column(db.Integer, nullable=True, default=0)
    games_team2_won = db.Column(db.Integer, nullable=True, default=0)

    team1 = db.relationship("Team", foreign_keys=[team1_id])
    team2 = db.relationship("Team", foreign_keys=[team2_id])
    actual_winner = db.relationship("Team", foreign_keys=[actual_winner_team_id])

    # FIXED: Points to BracketPick, and uses back_populates="series"
    picks_for_series = db.relationship(
        "BracketPick", back_populates="series", lazy="dynamic"
    )


class BracketSubmission(db.Model):
    __tablename__ = "bracket_submission"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    submission_timestamp = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    bracket_name = db.Column(db.String(100), nullable=True)

    # FIXED: Points to BracketPick
    picks = db.relationship(
        "BracketPick",
        backref="submission",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )


class BracketPick(db.Model):
    __tablename__ = "bracket_pick"
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey("bracket_submission.id"), nullable=False
    )
    series_id = db.Column(db.Integer, db.ForeignKey("series.id"), nullable=False)
    predicted_winner_team_id = db.Column(
        db.Integer, db.ForeignKey("team.id"), nullable=False
    )
    predicted_series_length = db.Column(db.Integer, nullable=False)

    # FIXED: Relationship name is now 'series' to match app.py logic
    series = db.relationship("Series", back_populates="picks_for_series")
    predicted_winner = db.relationship("Team", foreign_keys=[predicted_winner_team_id])
