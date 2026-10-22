from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.domain.models import GameRound


class TrainingStatus(StrEnum):
    OPEN = "offen"
    COMPLETED = "erledigt"
    COMPLETED_LATE = "verspätet erledigt"
    OVERDUE = "Frist überschritten"


ZURICH = ZoneInfo("Europe/Zurich")


@dataclass(frozen=True)
class TeamAggregation:
    participant_count: int
    total_score: int
    total_errors: int


def best_attempt(attempts: tuple[GameRound, ...]) -> GameRound:
    completed = [attempt for attempt in attempts if attempt.completed_at is not None]
    if not completed:
        raise ValueError("Es gibt keinen abgeschlossenen Versuch")
    highest_score = max(attempt.score or 0 for attempt in completed)
    highest_scoring = [
        attempt for attempt in completed if (attempt.score or 0) == highest_score
    ]
    return min(highest_scoring, key=lambda attempt: attempt.completed_at)


def team_aggregation(
    attempts: tuple[GameRound, ...],
) -> TeamAggregation | None:
    completed_by_employee: dict[str, list[GameRound]] = {}
    for attempt in attempts:
        if attempt.completed_at is not None:
            completed_by_employee.setdefault(attempt.employee_id, []).append(attempt)
    if len(completed_by_employee) < 3:
        return None
    best = tuple(
        best_attempt(tuple(employee_attempts))
        for employee_attempts in completed_by_employee.values()
    )
    return TeamAggregation(
        participant_count=len(best),
        total_score=sum(attempt.score or 0 for attempt in best),
        total_errors=sum(
            len(attempt.scenarios) - (attempt.score or 0) for attempt in best
        ),
    )


def training_status(
    attempts: tuple[GameRound, ...], due_date: date, current_at: datetime
) -> TrainingStatus:
    passed = tuple(
        attempt for attempt in attempts if attempt.completed_at and attempt.passed
    )
    if not passed:
        deadline = datetime.combine(due_date, time.max, tzinfo=ZURICH)
        return (
            TrainingStatus.OPEN
            if current_at.astimezone(ZURICH) <= deadline
            else TrainingStatus.OVERDUE
        )

    first_passed = min(passed, key=lambda attempt: attempt.completed_at)
    deadline = datetime.combine(due_date, time.max, tzinfo=ZURICH)
    if first_passed.completed_at.astimezone(ZURICH) > deadline:
        return TrainingStatus.COMPLETED_LATE
    return TrainingStatus.COMPLETED
