from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.domain.models import AnswerOption, GameRound, Scenario
from app.domain.rules import TrainingStatus, best_attempt, training_status

ZURICH = ZoneInfo("Europe/Zurich")


def make_scenario(scenario_id: str, *, active: bool = True) -> Scenario:
    return Scenario.create(
        id=scenario_id,
        situation=f"Situation {scenario_id}",
        explanation="Erklärung",
        legal_basis="InfoDG SO (Artikel zu prüfen)",
        options=(
            AnswerOption("right", "Richtig", True),
            AnswerOption("wrong-1", "Falsch 1", False),
            AnswerOption("wrong-2", "Falsch 2", False),
        ),
        active=active,
    )


def make_round() -> GameRound:
    scenarios = tuple(make_scenario(f"scenario-{number}") for number in range(1, 6))
    return GameRound.start(
        id="round-1",
        employee_id="employee-1",
        assignment_id="assignment-1",
        attempt_number=1,
        scenarios=scenarios,
    )


def test_scenario_requires_three_to_four_options_and_one_correct_answer():
    with pytest.raises(ValueError):
        Scenario.create(
            id="scenario-1",
            situation="Situation",
            explanation="Erklärung",
            legal_basis="Rechtsgrundlage",
            options=(AnswerOption("only", "Option", True),),
        )

    with pytest.raises(ValueError):
        Scenario.create(
            id="scenario-2",
            situation="Situation",
            explanation="Erklärung",
            legal_basis="Rechtsgrundlage",
            options=(
                AnswerOption("a", "A", True),
                AnswerOption("b", "B", True),
                AnswerOption("c", "C", False),
            ),
        )


def test_scenario_content_is_immutable_but_can_be_deactivated():
    scenario = make_scenario("scenario-1")

    with pytest.raises((AttributeError, TypeError)):
        scenario.situation = "Geändert"

    with pytest.raises((AttributeError, TypeError)):
        scenario.options[0].text = "Geändert"

    scenario.deactivate()
    assert scenario.active is False


def test_new_round_requires_exactly_five_active_scenarios():
    scenarios = tuple(make_scenario(f"scenario-{number}") for number in range(1, 5))

    with pytest.raises(ValueError):
        GameRound.start(
            id="round-1",
            employee_id="employee-1",
            assignment_id="assignment-1",
            attempt_number=1,
            scenarios=scenarios,
        )

    inactive = make_scenario("scenario-5", active=False)
    with pytest.raises(ValueError):
        GameRound.start(
            id="round-1",
            employee_id="employee-1",
            assignment_id="assignment-1",
            attempt_number=1,
            scenarios=(*scenarios, inactive),
        )


def test_round_scores_answer_and_returns_immediate_feedback():
    game_round = make_round()

    feedback = game_round.answer(
        position=1,
        option_id="right",
        answered_at=datetime(2026, 10, 21, 10, 0, tzinfo=ZURICH),
    )

    assert feedback.correct is True
    assert feedback.explanation == "Erklärung"
    assert feedback.legal_basis == "InfoDG SO (Artikel zu prüfen)"
    assert game_round.answers[1].option_id == "right"


def test_answer_must_belong_to_position_and_position_can_only_be_answered_once():
    game_round = make_round()
    answered_at = datetime(2026, 10, 21, 10, 0, tzinfo=ZURICH)

    with pytest.raises(ValueError):
        game_round.answer(position=1, option_id="missing", answered_at=answered_at)

    game_round.answer(position=1, option_id="right", answered_at=answered_at)
    with pytest.raises(ValueError):
        game_round.answer(position=1, option_id="right", answered_at=answered_at)


def test_round_completes_at_four_of_five_and_stores_score_and_pass_status():
    game_round = make_round()
    answered_at = datetime(2026, 10, 21, 10, 0, tzinfo=ZURICH)

    for position in range(1, 5):
        game_round.answer(position, "right", answered_at)
    game_round.answer(5, "wrong-1", answered_at)
    result = game_round.complete(datetime(2026, 10, 21, 10, 5, tzinfo=ZURICH))

    assert result.score == 4
    assert result.passed is True
    assert game_round.score == 4
    assert game_round.passed is True
    assert game_round.completed_at == datetime(2026, 10, 21, 10, 5, tzinfo=ZURICH)


def test_round_with_three_correct_answers_is_not_passed():
    game_round = make_round()
    answered_at = datetime(2026, 10, 21, 10, 0, tzinfo=ZURICH)

    for position in range(1, 4):
        game_round.answer(position, "right", answered_at)
    for position in range(4, 6):
        game_round.answer(position, "wrong-1", answered_at)

    result = game_round.complete(answered_at)

    assert result.score == 3
    assert result.passed is False
    assert game_round.passed is False


def test_best_attempt_uses_highest_score_then_earliest_completion():
    first = make_round()
    for position in range(1, 5):
        first.answer(position, "right", datetime(2026, 10, 21, 9, 0, tzinfo=ZURICH))
    first.answer(5, "wrong-1", datetime(2026, 10, 21, 9, 0, tzinfo=ZURICH))
    first.complete(datetime(2026, 10, 21, 10, 0, tzinfo=ZURICH))
    second = make_round()
    for position in range(1, 5):
        second.answer(position, "right", datetime(2026, 10, 21, 8, 0, tzinfo=ZURICH))
    second.answer(5, "wrong-1", datetime(2026, 10, 21, 8, 0, tzinfo=ZURICH))
    second.complete(datetime(2026, 10, 21, 9, 0, tzinfo=ZURICH))
    third = make_round()
    for position in range(1, 6):
        third.answer(position, "right", datetime(2026, 10, 21, 7, 0, tzinfo=ZURICH))
    third.complete(datetime(2026, 10, 21, 8, 0, tzinfo=ZURICH))

    assert best_attempt((first, second, third)) is third
    assert best_attempt((first, second)) is second


def test_training_status_uses_best_passed_attempt_and_due_date_until_local_day_end():
    completed = datetime(2026, 11, 30, 23, 59, 59, tzinfo=ZURICH)
    attempt = make_round()
    for position in range(1, 5):
        attempt.answer(position, "right", completed)
    attempt.answer(5, "wrong-1", completed)
    attempt.complete(completed)
    due_date = date(2026, 11, 30)

    assert training_status((attempt,), due_date, completed) is TrainingStatus.COMPLETED
    assert (
        training_status((), due_date, datetime(2026, 12, 1, 0, 0, tzinfo=ZURICH))
        is TrainingStatus.OVERDUE
    )

    late = make_round()
    late_at = datetime(2026, 12, 1, 0, 0, tzinfo=ZURICH)
    for position in range(1, 5):
        late.answer(position, "right", late_at)
    late.answer(5, "wrong-1", late_at)
    late.complete(late_at)
    assert (
        training_status((late,), due_date, late.completed_at)
        is TrainingStatus.COMPLETED_LATE
    )


def test_training_status_uses_first_of_two_equal_late_passed_attempts():
    due_date = date(2026, 11, 30)
    first = make_round()
    first_at = datetime(2026, 12, 1, 0, 1, tzinfo=ZURICH)
    second = make_round()
    second_at = datetime(2026, 12, 1, 0, 2, tzinfo=ZURICH)
    for attempt, answered_at in ((first, first_at), (second, second_at)):
        for position in range(1, 5):
            attempt.answer(position, "right", answered_at)
        attempt.answer(5, "wrong-1", answered_at)
        attempt.complete(answered_at)

    assert (
        training_status((second, first), due_date, second_at)
        is TrainingStatus.COMPLETED_LATE
    )


def test_training_status_keeps_completed_when_better_attempt_follows_after_deadline():
    due_date = date(2026, 11, 30)
    on_time = make_round()
    on_time_at = datetime(2026, 11, 30, 18, 0, tzinfo=ZURICH)
    for position in range(1, 5):
        on_time.answer(position, "right", on_time_at)
    on_time.answer(5, "wrong-1", on_time_at)
    on_time.complete(on_time_at)
    better = make_round()
    better_at = datetime(2026, 12, 5, 9, 0, tzinfo=ZURICH)
    for position in range(1, 6):
        better.answer(position, "right", better_at)
    better.complete(better_at)

    assert (
        training_status((better, on_time), due_date, better_at)
        is TrainingStatus.COMPLETED
    )
