from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.domain.models import (
    AnswerOption,
    Assignment,
    EvidenceRecord,
    GameRound,
    Scenario,
)
from app.domain.rules import team_aggregation


ZURICH = ZoneInfo("Europe/Zurich")


def scenarios():
    return tuple(
        Scenario.create(
            id=f"scenario-{number}",
            situation="Situation",
            explanation="Erklärung",
            legal_basis="Rechtsgrundlage",
            options=(
                AnswerOption("right", "Richtig", True),
                AnswerOption("wrong-1", "Falsch", False),
                AnswerOption("wrong-2", "Falsch", False),
            ),
        )
        for number in range(1, 6)
    )


def completed_round(employee_id: str, score: int, completed_at: datetime):
    game_round = GameRound.start(
        id=f"round-{employee_id}-{completed_at.isoformat()}",
        employee_id=employee_id,
        assignment_id="assignment-1",
        attempt_number=1,
        scenarios=scenarios(),
    )
    for position in range(1, 6):
        option_id = "right" if position <= score else "wrong-1"
        game_round.answer(position, option_id, completed_at)
    game_round.complete(completed_at)
    return game_round


def test_assignment_requires_module_department_and_local_date():
    assignment = Assignment(
        id="assignment-1",
        module_id="module-1",
        department_id="department-1",
        due_date=date(2026, 12, 31),
    )

    assert assignment.module_id == "module-1"

    with pytest.raises(ValueError):
        Assignment("assignment-2", "", "department-1", date(2026, 12, 31))
    with pytest.raises(ValueError):
        Assignment("assignment-3", "module-1", "", date(2026, 12, 31))
    with pytest.raises(ValueError):
        Assignment("assignment-4", "module-1", "department-1", datetime.now(ZURICH))


def test_team_aggregation_requires_three_different_completed_people():
    completed = completed_round(
        "employee-1", 5, datetime(2026, 10, 21, 9, tzinfo=ZURICH)
    )

    assert team_aggregation((completed,)) is None
    assert team_aggregation((completed, completed)) is None


def test_team_aggregation_uses_best_attempt_per_person_and_counts_errors():
    first = completed_round("employee-1", 3, datetime(2026, 10, 21, 9, tzinfo=ZURICH))
    best = completed_round("employee-1", 5, datetime(2026, 10, 21, 10, tzinfo=ZURICH))
    second = completed_round("employee-2", 4, datetime(2026, 10, 21, 11, tzinfo=ZURICH))
    third = completed_round("employee-3", 3, datetime(2026, 10, 21, 12, tzinfo=ZURICH))

    result = team_aggregation((first, best, second, third))

    assert result is not None
    assert result.participant_count == 3
    assert result.total_score == 12
    assert result.total_errors == 3


def test_team_aggregation_tie_uses_first_completed_best_attempt():
    first = completed_round("employee-1", 4, datetime(2026, 10, 21, 9, tzinfo=ZURICH))
    later = completed_round("employee-1", 4, datetime(2026, 10, 21, 10, tzinfo=ZURICH))
    second = completed_round("employee-2", 4, datetime(2026, 10, 21, 11, tzinfo=ZURICH))
    third = completed_round("employee-3", 4, datetime(2026, 10, 21, 12, tzinfo=ZURICH))

    result = team_aggregation((later, second, third, first))

    assert result is not None
    assert result.total_score == 12
    assert result.total_errors == 3


def test_evidence_record_contains_no_scores_or_errors_and_is_immutable():
    evidence = EvidenceRecord(
        employee_id="employee-1",
        module_id="module-1",
        completed_at=datetime(2026, 10, 21, 14, 5, tzinfo=ZURICH),
    )

    assert evidence.employee_id == "employee-1"
    assert not hasattr(evidence, "score")
    with pytest.raises((AttributeError, TypeError)):
        evidence.module_id = "module-2"
