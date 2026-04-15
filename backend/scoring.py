from flask import current_app
from models import db, BracketSubmission, Pick, Series, Team

# Tier 1: Base points for picking the correct winner
POINTS_WINNER = {
    1: 10,  # Round 1
    2: 15,  # Round 2
    3: 20,  # Conference Finals
    4: 40,  # Stanley Cup Final
}

# Tier 2: Additional bonus points for correct series length
# (ONLY awarded if the winner is also correct)
POINTS_LENGTH_BONUS = {
    1: 3,  # Round 1
    2: 5,  # Round 2
    3: 10,  # Conference Finals
    4: 20,  # Stanley Cup Final
}


def calculate_submission_stats(submission_id: int) -> dict:
    """
    Calculates score based on 2026 layered logic:
    1. Points for correct winner (10, 15, 20, 40)
    2. Bonus points for correct length (3, 5, 10, 20) IF winner is correct.
    """
    submission = BracketSubmission.query.get(submission_id)
    if not submission:
        current_app.logger.warning(f"Submission ID {submission_id} not found.")
        return {
            "score": 0,
            "correct_picks_for_completed": 0,
            "total_completed_series_in_playoffs": 0,
            "percentage_correct": 0.0,
        }

    total_score = 0
    correct_winners = 0

    all_db_series = Series.query.all()
    total_completed_series_in_playoffs = sum(
        1
        for s in all_db_series
        if s.status == "COMPLETED" and s.actual_winner_team_id is not None
    )

    for pick in submission.picks:
        series = next((s for s in all_db_series if s.id == pick.series_id), None)

        if series and series.status == "COMPLETED":
            winner_matches = (
                pick.predicted_winner_team_id == series.actual_winner_team_id
            )
            length_matches = pick.predicted_series_length == series.actual_series_length

            if winner_matches:
                # Award Base Points
                total_score += POINTS_WINNER.get(series.round_number, 0)
                correct_winners += 1

                # Award Length Bonus only if winner was correct
                if length_matches:
                    total_score += POINTS_LENGTH_BONUS.get(series.round_number, 0)
                    current_app.logger.info(
                        f"Bonus! {submission.bracket_name} nailed length for {series.series_identifier}"
                    )

    percentage_correct = 0.0
    if total_completed_series_in_playoffs > 0:
        percentage_correct = round(
            (correct_winners / total_completed_series_in_playoffs) * 100, 1
        )

    return {
        "score": total_score,
        "correct_picks_for_completed": correct_winners,
        "total_completed_series_in_playoffs": total_completed_series_in_playoffs,
        "percentage_correct": percentage_correct,
    }


def get_stanley_cup_pick_details_for_submission(submission_id: int) -> dict | None:
    submission = BracketSubmission.query.get(submission_id)
    if not submission:
        return None

    scf_series = Series.query.filter_by(series_identifier="SCF").first()
    if not scf_series:
        return None

    scf_pick = Pick.query.filter_by(
        submission_id=submission.id, series_id=scf_series.id
    ).first()

    if scf_pick and scf_pick.predicted_winner_team_id:
        predicted_winner_team = Team.query.get(scf_pick.predicted_winner_team_id)
        if predicted_winner_team:
            return {
                "team_abbr": predicted_winner_team.abbreviation,
                "logo_url": predicted_winner_team.logo_url,
                "predicted_length": scf_pick.predicted_series_length,
            }
    return None
