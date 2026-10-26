from dataclasses import replace
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.application.models import (
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
    GetDisplayNames,
    GetOverallEvaluation,
    GetPersonalStatus,
    ListAssignments,
)
from app.domain.models import AnswerOption, Assignment, GameRound, Scenario

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
    items = (ModuleRecord("module-a", "Modul A"),)

    def get(self, module_id):
        return next((item for item in self.items if item.id == module_id), None)

    def all(self):
        return self.items


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


def test_personal_status_ignores_rounds_of_other_people():
    assignments = FakeAssignments(
        [Assignment("a", "module-a", "department-a", date(2026, 12, 31))]
    )
    other = completed_round("employee-2", 5, datetime(2026, 10, 21, 10, tzinfo=ZURICH))
    status = GetPersonalStatus(assignments, FakeRounds((other,)), FakeClock()).execute(
        employee()
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

    assert result[0].available is False
    assert result[0].message == "zu wenige Teilnehmende"


def test_data_protection_officer_gets_overall_evaluation():
    assignments = FakeAssignments(
        [Assignment("a", "module-a", "department-a", date(2026, 12, 31))]
    )

    result = GetOverallEvaluation(
        assignments, FakeEmployees(), FakeDepartments(), FakeRounds(), FakeClock()
    ).execute(employee(Role.DATA_PROTECTION_OFFICER))

    assert [item.department_id for item in result.departments] == [
        "department-a",
        "department-b",
    ]


class EvidenceEmployees(FakeEmployees):
    items = (
        EmployeeRecord("employee-1", "department-a", "Zora", "Alt"),
        EmployeeRecord("employee-2", "department-a", "Anna", "Berg"),
    )


class EvidenceDepartments(FakeDepartments):
    items = (DepartmentRecord("department-a", "Einwohnerdienste"),)


def test_evidence_export_lists_every_attempt_with_names_and_scenarios():
    assignments = FakeAssignments(
        [Assignment("a", "module-a", "department-a", date(2026, 12, 31))]
    )
    passed = completed_round(
        "employee-1", 5, datetime(2026, 10, 21, 14, 5, tzinfo=ZURICH)
    )
    failed = completed_round("employee-2", 3, datetime(2026, 10, 21, 9, tzinfo=ZURICH))
    open_round = replace(
        completed_round("employee-1", 5, datetime(2026, 10, 21, 15, tzinfo=ZURICH)),
        id="round-open",
        attempt_number=2,
        answers={},
        completed_at=None,
        score=None,
        passed=None,
    )

    result = ExportTrainingEvidence(
        assignments,
        FakeRounds((open_round, passed, failed)),
        EvidenceEmployees(),
        EvidenceDepartments(),
        FakeModules(),
    ).execute(employee(Role.DATA_PROTECTION_OFFICER), "a")

    assert [(row.person, row.attempt_number, row.status) for row in result] == [
        ("Anna Berg", 1, "abgeschlossen"),
        ("Zora Alt", 1, "abgeschlossen"),
        ("Zora Alt", 2, "offen"),
    ]
    assert result[0].department == "Einwohnerdienste"
    assert result[0].module == "Modul A"
    assert (result[0].score, result[0].passed) == (3, False)
    assert (result[2].score, result[2].passed, result[2].completed_at) == (
        None,
        None,
        None,
    )
    assert result[1].scenario_ids == tuple(f"scenario-{n}" for n in range(1, 6))


def test_evidence_export_is_only_for_data_protection_officer():
    use_case = ExportTrainingEvidence(
        FakeAssignments(
            [Assignment("a", "module-a", "department-a", date(2026, 12, 31))]
        ),
        FakeRounds(),
        EvidenceEmployees(),
        EvidenceDepartments(),
        FakeModules(),
    )
    with pytest.raises(AccessDenied):
        use_case.execute(employee(Role.DEPARTMENT_LEAD), "a")


def test_personal_status_returns_each_assignment():
    assignments = FakeAssignments(
        [
            Assignment("a", "module-a", "department-a", date(2026, 12, 31)),
            Assignment("b", "module-b", "department-a", date(2026, 12, 31)),
        ]
    )
    result = GetPersonalStatus(assignments, FakeRounds(), FakeClock()).execute(
        employee()
    )
    assert [item.assignment_id for item in result] == ["a", "b"]


def test_department_status_returns_each_assignment_for_each_person():
    assignments = FakeAssignments(
        [
            Assignment("a", "module-a", "department-a", date(2026, 12, 31)),
            Assignment("b", "module-b", "department-a", date(2026, 12, 31)),
        ]
    )
    result = GetDepartmentStatus(
        assignments, FakeEmployees(), FakeRounds(), FakeClock()
    ).execute(employee(Role.DEPARTMENT_LEAD), "department-a")
    assert len(result.persons) == 6
    assert {person.assignment_id for person in result.persons} == {"a", "b"}


def test_team_aggregation_is_separate_for_each_assignment():
    assignments = FakeAssignments(
        [
            Assignment("a", "module-a", "department-a", date(2026, 12, 31)),
            Assignment("b", "module-b", "department-a", date(2026, 12, 31)),
        ]
    )
    rounds = FakeRounds(
        tuple(
            completed_round(employee_id, 5, datetime(2026, 10, 21, 12, tzinfo=ZURICH))
            for employee_id in ("employee-1", "employee-2", "employee-3")
        )
    )
    for item in rounds.items:
        item.assignment_id = "a"
    result = CreateTeamAggregation(assignments, rounds, FakeClock()).execute(
        employee(Role.DEPARTMENT_LEAD), "department-a"
    )
    assert {item.assignment_id for item in result} == {"a", "b"}


def test_list_assignments_is_only_for_data_protection_officer():
    assignments = FakeAssignments(
        [Assignment("a", "module-a", "department-a", date(2026, 12, 31))]
    )
    use_case = ListAssignments(assignments, FakeModules(), FakeDepartments())

    result = use_case.execute(employee(Role.DATA_PROTECTION_OFFICER))

    assert [item.id for item in result.assignments] == ["a"]
    assert [item.id for item in result.modules] == ["module-a"]
    assert [item.id for item in result.departments] == ["department-a", "department-b"]
    for role in (Role.EMPLOYEE, Role.DEPARTMENT_LEAD):
        with pytest.raises(AccessDenied):
            use_case.execute(employee(role))


class NamedEmployees(FakeEmployees):
    items = (
        EmployeeRecord("employee-1", "department-a", "Ada", "Muster"),
        EmployeeRecord("employee-9", "department-b", "Bea", "Beispiel"),
    )


class NamedDepartments(FakeDepartments):
    items = (
        DepartmentRecord("department-a", "Abteilung A"),
        DepartmentRecord("department-b", "Abteilung B"),
    )


def test_display_names_follow_role_visibility():
    use_case = GetDisplayNames(NamedEmployees(), FakeModules(), NamedDepartments())

    lead = use_case.execute(employee(Role.DEPARTMENT_LEAD))
    officer = use_case.execute(employee(Role.DATA_PROTECTION_OFFICER))
    own = use_case.execute(employee(Role.EMPLOYEE))

    assert lead.employees == {"employee-1": "Ada Muster"}
    assert lead.departments == {"department-a": "Abteilung A"}
    assert officer.employees == {
        "employee-1": "Ada Muster",
        "employee-9": "Bea Beispiel",
    }
    assert officer.departments == {
        "department-a": "Abteilung A",
        "department-b": "Abteilung B",
    }
    assert own.employees == {"employee-1": "Ada Muster"}
    assert own.modules == {"module-a": "Modul A"}


class MixedRoleEmployees(FakeEmployees):
    items = (
        EmployeeRecord("lead-a", "department-a", role=Role.DEPARTMENT_LEAD),
        EmployeeRecord("employee-1", "department-a"),
        EmployeeRecord("officer", "department-b", role=Role.DATA_PROTECTION_OFFICER),
        EmployeeRecord("employee-2", "department-b"),
    )


def test_department_status_lists_only_employees_who_must_train():
    assignments = FakeAssignments(
        [Assignment("a", "module-a", "department-a", date(2026, 12, 31))]
    )
    result = GetDepartmentStatus(
        assignments, MixedRoleEmployees(), FakeRounds(), FakeClock()
    ).execute(employee(Role.DEPARTMENT_LEAD), "department-a")

    assert [person.employee_id for person in result.persons] == ["employee-1"]


def test_overall_evaluation_lists_only_employees_who_must_train():
    assignments = FakeAssignments(
        [
            Assignment("a", "module-a", "department-a", date(2026, 12, 31)),
            Assignment("b", "module-a", "department-b", date(2026, 12, 31)),
        ]
    )
    result = GetOverallEvaluation(
        assignments,
        MixedRoleEmployees(),
        FakeDepartments(),
        FakeRounds(),
        FakeClock(),
    ).execute(employee(Role.DATA_PROTECTION_OFFICER))

    assert {
        department.department_id: [person.employee_id for person in department.persons]
        for department in result.departments
    } == {"department-a": ["employee-1"], "department-b": ["employee-2"]}
