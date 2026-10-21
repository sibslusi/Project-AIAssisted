from datetime import date, datetime
from typing import Protocol

from app.application.models import Assignment
from app.domain.models import GameRound, Scenario


class AssignmentRepository(Protocol):
    def for_department(self, department_id: str) -> tuple[Assignment, ...]: ...

    def get(self, assignment_id: str) -> Assignment | None: ...


class ScenarioRepository(Protocol):
    def for_module(self, module_id: str) -> tuple[Scenario, ...]: ...


class GameRoundRepository(Protocol):
    def get(self, round_id: str) -> GameRound | None: ...

    def open_for(self, employee_id: str, assignment_id: str) -> GameRound | None: ...

    def next_attempt_number(self, employee_id: str, assignment_id: str) -> int: ...

    def save(self, game_round: GameRound) -> None: ...

    def for_assignment(self, assignment_id: str) -> tuple[GameRound, ...]: ...


class CurrentActorPort(Protocol):
    def current_actor(self): ...


class ClockPort(Protocol):
    def now(self) -> datetime: ...

    def today(self) -> date:
        return self.now().date()
