from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.application.models import (
    Assignment,
    DepartmentRecord,
    EmployeeRecord,
    ModuleRecord,
    Role,
)
from app.application.ports import ClockPort
from app.application.use_cases import (
    AccessDenied,
    AssignModule,
    CreateTeamAggregation,
    ExportTrainingEvidence,
    GetDepartmentStatus,
    GetOverallEvaluation,
    GetPersonalStatus,
)
from app.domain.models import AnswerOption, GameRound, Scenario

ZURICH = ZoneInfo("Europe/Zurich")


class FakeClock(ClockPort):
    def now(self):
        return datetime(2026, 10, 21, 12, tzinfo=ZURICH)


class FakeAssignments:
    def __init__(self, items=()):
        self.items = list(items)

    def for_department(self, department_id):
        return tuple(item for item in self.items if item.department_id == department_id)

    def for_employee(self, employee_id):
        return tuple(
            item for item in self.items if item.department_id == "department-a"
        )

    def all(self):
        return tuple(self.items)

    def get(self, assignment_id):
        return next((item for item in self.items if item.id == assignment_id), None)

    def save(self, assignment):
        self.items.append(assignment)
        return assignment


class FakeEmployees:
    items = (
        EmployeeRecord("employee-1", "department-a"),
        EmployeeRecord("employee-2", "department-a"),
        EmployeeRecord("employee-3", "department-a"),
    )

    def get(self, employee_id):
        return next((item for item in self.items if item.id == employee_id), None)

    def for_department(self, department_id):
        return tuple(item for item in self.items if item.department_id == department_id)

    def all(self):
        return self.items


class FakeDepartments:
    items = (DepartmentRecord("department-a"), DepartmentRecord("department-b"))

    def get(self, department_id):
        return next((item for item in self.items if item.id == department_id), None)

    def all(self):
        return self.items


class FakeModules:
    def get(self, module_id):
        return ModuleRecord(module_id) if module_id == "module-a" else None


class FakeRounds:
    def __init__(self, items=()):
        self.items = list(items)

    def for_assignment(self, assignment_id):
        return tuple(item for item in self.items if item.assignment_id == assignment_id)


def completed_round(employee_id, score, completed_at):
    game_round = GameRound.start(
        id=f"round-{employee_id}",
        employee_id=employee_id,
        assignment_id="a",
        attempt_number=1,
        scenarios=tuple(
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
        ),
    )
    for position in range(1, 6):
        game_round.answer(
            position, "right" if position <= score else "wrong-1", completed_at
        )
    game_round.complete(completed_at)
    return game_round


def employee(role=Role.EMPLOYEE, department_id="department-a"):
    return __import__("app.application.models", fromlist=["Actor"]).Actor(
        "employee-1", role, department_id
    )


def test_assign_module_requires_officer_and_validates_references():
    assignments = FakeAssignments()
    use_case = AssignModule(assignments, FakeModules(), FakeDepartments())

    result = use_case.execute(
        employee(Role.DATA_PROTECTION_OFFICER),
        "module-a",
        "department-a",
        date(2026, 12, 31),
    )

    assert result.module_id == "module-a"
    with pytest.raises(AccessDenied):
        use_case.execute(employee(), "module-a", "department-a", date(2026, 12, 31))


def test_personal_status_is_limited_to_own_assignments():
    assignments = FakeAssignments(
        [Assignment("a", "module-a", "department-a", date(2026, 12, 31))]
    )
    status = GetPersonalStatus(assignments, FakeRounds(), FakeClock()).execute(
        employee(),
    )

    assert status[0].status == "offen"
    assert status[0].score is None


def test_department_status_has_person_status_without_individual_scores():
    assignments = FakeAssignments(
        [Assignment("a", "module-a", "department-a", date(2026, 12, 31))]
    )
    result = GetDepartmentStatus(
        assignments, FakeEmployees(), FakeRounds(), FakeClock()
    ).execute(employee(Role.DEPARTMENT_LEAD), "department-a")

    assert len(result.persons) == 3
    assert not hasattr(result.persons[0], "score")


def test_team_aggregation_is_available_only_for_three_people():
    assignments = FakeAssignments(
        [Assignment("a", "module-a", "department-a", date(2026, 12, 31))]
    )
    result = CreateTeamAggregation(assignments, FakeRounds(), FakeClock()).execute(
        employee(Role.DEPARTMENT_LEAD), "department-a"
    )

    assert result.available is False
    assert result.message == "zu wenige Teilnehmende"


def test_data_protection_officer_gets_overall_evaluation():
    assignments = FakeAssignments(
        [Assignment("a", "module-a", "department-a", date(2026, 12, 31))]
    )

    result = GetOverallEvaluation(
        assignments, FakeEmployees(), FakeRounds(), FakeClock()
    ).execute(employee(Role.DATA_PROTECTION_OFFICER))

    assert [item.department_id for item in result.departments] == [
        "department-a",
        "department-b",
    ]


def test_evidence_export_contains_person_module_and_completion_only():
    assignments = FakeAssignments(
        [Assignment("a", "module-a", "department-a", date(2026, 12, 31))]
    )
    completed = completed_round(
        "employee-1", 5, datetime(2026, 10, 21, 14, 5, tzinfo=ZURICH)
    )
    result = ExportTrainingEvidence(assignments, FakeRounds((completed,))).execute(
        employee(Role.DATA_PROTECTION_OFFICER), "a"
    )

    assert result[0].module_id == "module-a"
    assert not hasattr(result[0], "score")
