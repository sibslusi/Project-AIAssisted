from uuid import uuid4

from app.application.models import (
    Actor,
    AssignedModule,
    ProgressView,
    Role,
    RoundView,
)
from app.application.ports import (
    AssignmentRepository,
    ClockPort,
    GameRoundRepository,
    ScenarioRepository,
)
from app.domain.models import GameRound
from app.domain.rules import best_attempt


class AccessDenied(Exception):
    pass


class NotFound(Exception):
    pass


class InvalidRequest(Exception):
    pass


def _assignment_for_actor(
    assignments: AssignmentRepository, actor: Actor, module_id: str
):
    matching = tuple(
        assignment
        for assignment in assignments.for_department(actor.department_id)
        if assignment.module_id == module_id
    )
    return matching[0] if matching else None


class ListAssignedModules:
    def __init__(self, assignments: AssignmentRepository, rounds: GameRoundRepository):
        self.assignments = assignments
        self.rounds = rounds

    def execute(self, actor: Actor) -> tuple[AssignedModule, ...]:
        return tuple(
            AssignedModule(item.id, item.module_id, item.due_date)
            for item in self.assignments.for_department(actor.department_id)
        )


class StartOrResumeGameRound:
    def __init__(
        self,
        assignments: AssignmentRepository,
        scenarios: ScenarioRepository,
        rounds: GameRoundRepository,
    ):
        self.assignments = assignments
        self.scenarios = scenarios
        self.rounds = rounds

    def execute(self, actor: Actor, module_id: str) -> RoundView:
        if actor.role is not Role.EMPLOYEE:
            raise AccessDenied("Nur Mitarbeitende dürfen Runden starten")
        assignment = _assignment_for_actor(self.assignments, actor, module_id)
        if assignment is None:
            raise NotFound("Modul nicht gefunden")
        existing = self.rounds.open_for(actor.id, assignment.id)
        if existing is not None:
            return _round_view(existing)
        game_round = GameRound.start(
            id=str(uuid4()),
            employee_id=actor.id,
            assignment_id=assignment.id,
            attempt_number=self.rounds.next_attempt_number(actor.id, assignment.id),
            scenarios=self.scenarios.for_module(module_id),
        )
        self.rounds.save(game_round)
        return _round_view(game_round)


class GetTrainingProgress:
    def __init__(
        self,
        assignments: AssignmentRepository,
        rounds: GameRoundRepository,
        clock: ClockPort,
    ):
        self.assignments = assignments
        self.rounds = rounds
        self.clock = clock

    def execute(self, actor: Actor, module_id: str) -> ProgressView:
        assignment = _assignment_for_actor(self.assignments, actor, module_id)
        if assignment is None:
            raise NotFound("Modul nicht gefunden")
        attempts = tuple(
            attempt
            for attempt in self.rounds.for_assignment(assignment.id)
            if actor.role is not Role.EMPLOYEE or attempt.employee_id == actor.id
        )
        if actor.role is Role.EMPLOYEE:
            return ProgressView(False, _own_score(attempts))
        completed = tuple(
            attempt for attempt in attempts if attempt.completed_at is not None
        )
        employees = {attempt.employee_id for attempt in completed}
        if len(employees) < 3:
            return ProgressView(False, None)
        scores = {
            employee_id: best_attempt(
                tuple(
                    attempt
                    for attempt in completed
                    if attempt.employee_id == employee_id
                )
            ).score
            for employee_id in employees
        }
        return ProgressView(True, scores)


class SubmitRoundAnswer:
    def __init__(
        self,
        assignments: AssignmentRepository,
        rounds: GameRoundRepository,
        clock: ClockPort,
    ):
        self.assignments = assignments
        self.rounds = rounds
        self.clock = clock

    def execute(self, actor: Actor, round_id: str, position: int, option_id: str):
        if actor.role is not Role.EMPLOYEE:
            raise AccessDenied("Nur Mitarbeitende dürfen Antworten übermitteln")
        game_round = self.rounds.get(round_id)
        if game_round is None or game_round.employee_id != actor.id:
            raise NotFound("Runde nicht gefunden")
        feedback = game_round.answer(position, option_id, self.clock.now())
        if game_round.first_open_position is None:
            game_round.complete(self.clock.now())
        self.rounds.save(game_round)
        return feedback


def _round_view(game_round: GameRound) -> RoundView:
    return RoundView(
        game_round.id,
        game_round.attempt_number,
        tuple(scenario.id for scenario in game_round.scenarios),
        game_round.first_open_position,
    )


def _own_score(attempts):
    completed = tuple(
        attempt for attempt in attempts if attempt.completed_at is not None
    )
    return None if not completed else {"best": best_attempt(completed).score}
