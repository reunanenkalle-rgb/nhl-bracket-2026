# backend/scoring.py

from flask import current_app  # For logging

# Import db instance and models from your new models.py
from models import db, BracketSubmission, Pick, Series, Team

# Define your scoring points per round
POINTS_PER_ROUND = {1: 10, 2: 20, 3: 40, 4: 80}


def calculate_submission_score(submission_id: int) -> int:
    submission = BracketSubmission.query.get(submission_id)
    if not submission:
        current_app.logger.warning(
            f"calculate_submission_score: Submission ID {submission_id} not found."
        )
        return 0

    total_score = 0
    current_app.logger.debug(
        f"Calculating score for submission ID: {submission_id}, Player ID: {submission.player_id}"
    )

    for pick in submission.picks:
        series = Series.query.get(pick.series_id)
        if series:
            current_app.logger.debug(
                f"  Processing pick for Series: {series.series_identifier} (DB ID: {series.id}), Round: {series.round_number}"
            )
            current_app.logger.debug(
                f"    User picked: {pick.predicted_winner_team_id}, Actual winner: {series.actual_winner_team_id}, Status: {series.status}"
            )

            if (
                series.status == "COMPLETED"
                and series.actual_winner_team_id is not None
            ):
                if pick.predicted_winner_team_id == series.actual_winner_team_id:
                    points_for_this_pick = POINTS_PER_ROUND.get(series.round_number, 0)
                    total_score += points_for_this_pick
                    current_app.logger.debug(
                        f"    Correct pick! Points added: {points_for_this_pick}. Current total: {total_score}"
                    )
                else:
                    current_app.logger.debug(f"    Incorrect pick.")
            else:
                current_app.logger.debug(
                    f"    Series not completed or no actual winner yet. No points for this pick."
                )
        else:
            current_app.logger.warning(
                f"    Could not find Series with ID: {pick.series_id} for a pick in submission {submission_id}."
            )

    current_app.logger.info(
        f"Total score for submission ID {submission_id}: {total_score}"
    )
    return total_score
