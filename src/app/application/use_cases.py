from uuid import uuid4

from app.application.models import (
    Actor,
    AssignedModule,
    Assignment,
    DepartmentStatus,
    EmployeeRecord,
    OverallEvaluation,
    PersonalStatus,
    PersonStatus,
    ProgressView,
    Role,
    RoundView,
    TeamAggregationView,
)
from app.application.ports import (
    AssignmentRepository,
    ClockPort,
    DepartmentRepository,
    EmployeeRepository,
    GameRoundRepository,
    ModuleRepository,
    ScenarioRepository,
)
from app.domain.models import EvidenceRecord, GameRound
from app.domain.rules import best_attempt, team_aggregation, training_status


class AccessDenied(Exception):
    pass


class NotFound(Exception):
    pass


class InvalidRequest(Exception):
    pass


class AssignModule:
    def __init__(
        self,
        assignments: AssignmentRepository,
        modules: ModuleRepository,
        departments: DepartmentRepository,
    ):
        self.assignments = assignments
        self.modules = modules
        self.departments = departments

    def execute(
        self, actor: Actor, module_id: str, department_id: str, due_date
    ) -> Assignment:
        if actor.role is not Role.DATA_PROTECTION_OFFICER:
            raise AccessDenied("Nur Datenschutzverantwortliche dürfen zuweisen")
        if self.modules.get(module_id) is None:
            raise NotFound("Modul nicht gefunden")
        if self.departments.get(department_id) is None:
            raise NotFound("Abteilung nicht gefunden")
        try:
            from app.domain.models import Assignment as DomainAssignment

            DomainAssignment(
                id=str(uuid4()),
                module_id=module_id,
                department_id=department_id,
                due_date=due_date,
            )
        except (TypeError, ValueError) as error:
            raise InvalidRequest(str(error)) from error
        return self.assignments.save(
            Assignment(str(uuid4()), module_id, department_id, due_date)
        )


def _status_and_score(attempts, assignment, clock):
    completed = tuple(
        attempt for attempt in attempts if attempt.completed_at is not None
    )
    return (
        training_status(attempts, assignment.due_date, clock.now()).value,
        None if not completed else best_attempt(completed).score,
    )


class GetPersonalStatus:
    def __init__(
        self,
        assignments: AssignmentRepository,
        rounds: GameRoundRepository,
        clock: ClockPort,
    ):
        self.assignments = assignments
        self.rounds = rounds
        self.clock = clock

    def execute(self, actor: Actor) -> tuple[PersonalStatus, ...]:
        if actor.role is not Role.EMPLOYEE:
            raise AccessDenied("Nur Mitarbeitende dürfen den persönlichen Status sehen")
        assignments = self.assignments.for_employee(actor.id)
        return tuple(
            PersonalStatus(
                assignment.id,
                assignment.module_id,
                status,
                score,
            )
            for assignment in assignments
            for status, score in (
                _status_and_score(
                    self.rounds.for_assignment(assignment.id), assignment, self.clock
                ),
            )
        )


class GetDepartmentStatus:
    def __init__(
        self,
        assignments: AssignmentRepository,
        employees: EmployeeRepository,
        rounds: GameRoundRepository,
        clock: ClockPort,
    ):
        self.assignments = assignments
        self.employees = employees
        self.rounds = rounds
        self.clock = clock

    def execute(self, actor: Actor, department_id: str) -> DepartmentStatus:
        if actor.role is not Role.DEPARTMENT_LEAD:
            raise AccessDenied(
                "Nur Abteilungsleitungen dürfen den Abteilungsstatus sehen"
            )
        if actor.department_id != department_id:
            raise AccessDenied("Fremde Abteilung")
        assignments = self.assignments.for_department(department_id)
        persons = tuple(
            PersonStatus(employee.id, status)
            for employee in self.employees.for_department(department_id)
            for status in (
                _person_status(employee, assignments, self.rounds, self.clock),
            )
        )
        return DepartmentStatus(department_id, persons)


def _person_status(employee: EmployeeRecord, assignments, rounds, clock) -> str:
    if not assignments:
        return "offen"
    statuses = [
        training_status(
            tuple(
                attempt
                for attempt in rounds.for_assignment(assignment.id)
                if attempt.employee_id == employee.id
            ),
            assignment.due_date,
            clock.now(),
        ).value
        for assignment in assignments
    ]
    return statuses[0]


class CreateTeamAggregation:
    def __init__(
        self,
        assignments: AssignmentRepository,
        rounds: GameRoundRepository,
        clock: ClockPort,
    ):
        self.assignments = assignments
        self.rounds = rounds
        self.clock = clock

    def execute(self, actor: Actor, department_id: str) -> TeamAggregationView:
        if actor.role is not Role.DEPARTMENT_LEAD:
            raise AccessDenied("Nur Abteilungsleitungen dürfen Teamwerte sehen")
        if actor.department_id != department_id:
            raise AccessDenied("Fremde Abteilung")
        assignments = self.assignments.for_department(department_id)
        attempts = tuple(
            attempt
            for assignment in assignments
            for attempt in self.rounds.for_assignment(assignment.id)
        )
        aggregation = team_aggregation(attempts)
        if aggregation is None:
            return TeamAggregationView(
                department_id, False, "zu wenige Teilnehmende", 0, None, None
            )
        return TeamAggregationView(
            department_id,
            True,
            None,
            aggregation.participant_count,
            aggregation.total_score,
            aggregation.total_errors,
        )


class GetOverallEvaluation:
    def __init__(self, assignments, employees, departments, rounds, clock):
        self.assignments = assignments
        self.employees = employees
        self.departments = departments
        self.rounds = rounds
        self.clock = clock

    def execute(self, actor: Actor) -> OverallEvaluation:
        if actor.role is not Role.DATA_PROTECTION_OFFICER:
            raise AccessDenied("Nur Datenschutzverantwortliche dürfen alles auswerten")
        departments = tuple(
            DepartmentStatus(
                department.id,
                tuple(
                    PersonStatus(
                        employee.id,
                        _person_status(
                            employee,
                            self.assignments.for_department(department.id),
                            self.rounds,
                            self.clock,
                        ),
                    )
                    for employee in self.employees.for_department(department.id)
                ),
            )
            for department in self.departments.all()
        )
        return OverallEvaluation(departments)


class ExportTrainingEvidence:
    def __init__(self, assignments, rounds):
        self.assignments = assignments
        self.rounds = rounds

    def execute(self, actor: Actor, assignment_id: str) -> tuple[EvidenceRecord, ...]:
        if actor.role is not Role.DATA_PROTECTION_OFFICER:
            raise AccessDenied(
                "Nur Datenschutzverantwortliche dürfen Nachweise exportieren"
            )
        assignment = self.assignments.get(assignment_id)
        if assignment is None:
            raise NotFound("Zuweisung nicht gefunden")
        by_employee: dict[str, list[GameRound]] = {}
        for attempt in self.rounds.for_assignment(assignment_id):
            if attempt.completed_at is not None:
                by_employee.setdefault(attempt.employee_id, []).append(attempt)
        return tuple(
            EvidenceRecord(
                employee_id,
                assignment.module_id,
                best_attempt(tuple(attempts)).completed_at,
                assignment.department_id,
            )
            for employee_id, attempts in by_employee.items()
        )


def _assignment_for_actor(
    assignments: AssignmentRepository, actor: Actor, module_id: str
):
    if actor.role is Role.DATA_PROTECTION_OFFICER:
        all_assignments = getattr(assignments, "all", None)
        candidates = (
            all_assignments()
            if all_assignments is not None
            else assignments.for_department(actor.department_id)
        )
    else:
        candidates = assignments.for_department(actor.department_id)
    matching = tuple(
        assignment for assignment in candidates if assignment.module_id == module_id
    )
    return matching[0] if matching else None


class ListAssignedModules:
    def __init__(self, assignments: AssignmentRepository, rounds: GameRoundRepository):
        self.assignments = assignments
        self.rounds = rounds

    def execute(self, actor: Actor) -> tuple[AssignedModule, ...]:
        assignments = (
            self.assignments.all()
            if actor.role is Role.DATA_PROTECTION_OFFICER
            else self.assignments.for_department(actor.department_id)
        )
        return tuple(
            AssignedModule(item.id, item.module_id, item.due_date)
            for item in assignments
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
            return ProgressView(
                False,
                _own_score(attempts),
                training_status(attempts, assignment.due_date, self.clock.now()).value,
            )
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
        return ProgressView(
            True,
            {"completed_people": len(scores), "total_score": sum(scores.values())},
        )


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
