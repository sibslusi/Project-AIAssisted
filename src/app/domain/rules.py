from datetime import date, datetime, time
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.domain.models import GameRound


class TrainingStatus(StrEnum):
    OPEN = "offen"
    COMPLETED = "bestanden"
    COMPLETED_LATE = "verspätet erledigt"
    OVERDUE = "Frist überschritten"


ZURICH = ZoneInfo("Europe/Zurich")


def best_attempt(attempts: tuple[GameRound, ...]) -> GameRound:
    completed = [attempt for attempt in attempts if attempt.completed_at is not None]
    if not completed:
        raise ValueError("Es gibt keinen abgeschlossenen Versuch")
    highest_score = max(attempt.score or 0 for attempt in completed)
    highest_scoring = [
        attempt for attempt in completed if (attempt.score or 0) == highest_score
    ]
    return min(highest_scoring, key=lambda attempt: attempt.completed_at)


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

    best_passed = best_attempt(passed)
    deadline = datetime.combine(due_date, time.max, tzinfo=ZURICH)
    if best_passed.completed_at.astimezone(ZURICH) > deadline:
        return TrainingStatus.COMPLETED_LATE
    return TrainingStatus.COMPLETED
