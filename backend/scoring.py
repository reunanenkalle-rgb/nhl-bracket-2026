# backend/scoring.py

from flask import current_app
from models import db, BracketSubmission, Pick, Series, Team  # Ensure Team is imported

POINTS_PER_ROUND = {1: 10, 2: 20, 3: 40, 4: 80}


def calculate_submission_stats(submission_id: int) -> dict:
    """
    Calculates score, number of correct picks for completed series,
    and total number of completed series in the playoffs.
    """
    submission = BracketSubmission.query.get(submission_id)
    if not submission:
        current_app.logger.warning(
            f"calculate_submission_stats: Submission ID {submission_id} not found."
        )
        return {
            "score": 0,
            "correct_picks_for_completed": 0,
            "total_completed_series_in_playoffs": 0,
            "percentage_correct": 0.0,
        }

    total_score = 0
    correct_picks_for_completed = 0

    # Get all series to count completed ones and to check against picks
    all_db_series = Series.query.all()

    # This will be the denominator for the percentage
    total_completed_series_in_playoffs = sum(
        1
        for s in all_db_series
        if s.status == "COMPLETED" and s.actual_winner_team_id is not None
    )

    for pick in submission.picks:
        series = next(
            (s for s in all_db_series if s.id == pick.series_id), None
        )  # Find series from pre-fetched list
        if series:
            if (
                series.status == "COMPLETED"
                and series.actual_winner_team_id is not None
            ):
                if pick.predicted_winner_team_id == series.actual_winner_team_id:
                    points_for_this_pick = POINTS_PER_ROUND.get(series.round_number, 0)
                    total_score += points_for_this_pick
                    correct_picks_for_completed += 1
        else:
            current_app.logger.warning(
                f"    Could not find Series with ID: {pick.series_id} for a pick in submission {submission_id}."
            )

    percentage_correct = 0.0
    if total_completed_series_in_playoffs > 0:
        percentage_correct = round(
            (correct_picks_for_completed / total_completed_series_in_playoffs) * 100, 1
        )

    current_app.logger.info(
        f"Stats for submission ID {submission_id}: Score={total_score}, CorrectPicks={correct_picks_for_completed}, TotalCompleted={total_completed_series_in_playoffs}"
    )
    return {
        "score": total_score,
        "correct_picks_for_completed": correct_picks_for_completed,
        "total_completed_series_in_playoffs": total_completed_series_in_playoffs,
        "percentage_correct": percentage_correct,
    }


def get_stanley_cup_pick_details_for_submission(submission_id: int) -> dict | None:
    """
    Finds the user's pick for the Stanley Cup Final and returns team abbreviation and logo.
    """
    submission = BracketSubmission.query.get(submission_id)
    if not submission:
        return None

    # Find the Stanley Cup Final series (assuming its identifier is 'SCF')
    scf_series = Series.query.filter_by(series_identifier="SCF").first()
    if not scf_series:
        current_app.logger.warning(
            "Stanley Cup Final series (SCF) not found in database."
        )
        return None

    # Find the user's pick for this SCF series
    scf_pick = Pick.query.filter_by(
        submission_id=submission.id, series_id=scf_series.id
    ).first()

    if scf_pick and scf_pick.predicted_winner_team_id:
        predicted_winner_team = Team.query.get(scf_pick.predicted_winner_team_id)
        if predicted_winner_team:
            return {
                "team_abbr": predicted_winner_team.abbreviation,
                "logo_url": predicted_winner_team.logo_url,
            }
        else:
            current_app.logger.warning(
                f"Could not find team with ID {scf_pick.predicted_winner_team_id} for SCF pick in submission {submission_id}"
            )
    return None
