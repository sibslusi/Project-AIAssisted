from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.application.models import Actor, Role
from app.application.ports import ClockPort
from app.application.use_cases import (
    AccessDenied,
    GetOpenGameRound,
    GetTrainingProgress,
    ListAssignedModules,
    NotFound,
    StartOrResumeGameRound,
    SubmitRoundAnswer,
)
from app.domain.models import AnswerOption, Assignment, GameRound, Scenario

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


class FakeAssignments:
    def __init__(self):
        self.items = (
            Assignment("assignment-a", "module-a", "department-a", date(2026, 11, 30)),
            Assignment("assignment-b", "module-b", "department-b", date(2026, 11, 30)),
        )

    def for_department(self, department_id):
        return tuple(item for item in self.items if item.department_id == department_id)

    def all(self):
        return self.items

    def get(self, assignment_id):
        return next((item for item in self.items if item.id == assignment_id), None)


class FakeScenarios:
    def for_module(self, module_id):
        return scenarios()


class FakeScenariosWithInactive:
    def for_module(self, module_id):
        return (
            *scenarios()[:4],
            Scenario.create(
                id="inactive",
                situation="Situation",
                explanation="Erklärung",
                legal_basis="Rechtsgrundlage",
                active=False,
                options=(
                    AnswerOption("right", "Richtig", True),
                    AnswerOption("wrong-1", "Falsch", False),
                    AnswerOption("wrong-2", "Falsch", False),
                ),
            ),
        )


class FakeRounds:
    def __init__(self, rounds=()):
        self.items = list(rounds)

    def open_for(self, employee_id, assignment_id):
        return next(
            (
                item
                for item in self.items
                if item.employee_id == employee_id
                and item.assignment_id == assignment_id
                and item.completed_at is None
            ),
            None,
        )

    def next_attempt_number(self, employee_id, assignment_id):
        return 1 + max(
            (
                item.attempt_number
                for item in self.items
                if item.employee_id == employee_id
                and item.assignment_id == assignment_id
            ),
            default=0,
        )

    def save(self, game_round):
        self.items.append(game_round)

    def for_assignment(self, assignment_id):
        return tuple(item for item in self.items if item.assignment_id == assignment_id)

    def get(self, round_id):
        return next((item for item in self.items if item.id == round_id), None)


class FakeClock(ClockPort):
    def __init__(self, current_at):
        self.current_at = current_at

    def now(self):
        return self.current_at


def employee(department_id="department-a"):
    return Actor("employee-1", Role.EMPLOYEE, department_id)


def test_employee_sees_only_assignments_of_own_department():
    result = ListAssignedModules(FakeAssignments()).execute(employee())

    assert [item.module_id for item in result] == ["module-a"]


def test_only_employees_can_start_a_round_and_foreign_department_is_hidden():
    assignments = FakeAssignments()
    round_repo = FakeRounds()
    start = StartOrResumeGameRound(assignments, FakeScenarios(), round_repo)

    with pytest.raises(AccessDenied):
        start.execute(Actor("lead-1", Role.DEPARTMENT_LEAD, "department-a"), "module-a")

    with pytest.raises(NotFound):
        start.execute(employee(), "module-b")


def test_start_creates_five_scenario_round_and_reuses_open_round():
    assignments = FakeAssignments()
    round_repo = FakeRounds()
    start = StartOrResumeGameRound(assignments, FakeScenarios(), round_repo)

    first = start.execute(employee(), "module-a")
    resumed = start.execute(employee(), "module-a")

    assert first.id == resumed.id
    assert first.attempt_number == 1
    assert len(first.scenario_ids) == 5


def test_open_round_lookup_never_creates_a_round():
    assignments = FakeAssignments()
    round_repo = FakeRounds()
    lookup = GetOpenGameRound(assignments, round_repo)

    assert lookup.execute(employee(), "module-a") is None
    assert round_repo.items == []

    started = StartOrResumeGameRound(assignments, FakeScenarios(), round_repo).execute(
        employee(), "module-a"
    )

    assert lookup.execute(employee(), "module-a").id == started.id
    lead = Actor("lead-1", Role.DEPARTMENT_LEAD, "department-a")
    with pytest.raises(AccessDenied):
        lookup.execute(lead, "module-a")
    with pytest.raises(NotFound):
        lookup.execute(employee(), "module-b")


def test_open_round_continues_at_first_unanswered_position():
    assignments = FakeAssignments()
    rounds = FakeRounds()
    start = StartOrResumeGameRound(assignments, FakeScenarios(), rounds)
    started = start.execute(employee(), "module-a")
    rounds.items[0].answer(1, "right", datetime(2026, 10, 21, tzinfo=ZURICH))
    resumed = start.execute(employee(), "module-a")

    assert resumed.id == started.id
    assert resumed.next_position == 2
    assert len(rounds.items) == 1


def test_repeated_round_gets_next_attempt_number():
    assignments = FakeAssignments()
    rounds = FakeRounds()
    start = StartOrResumeGameRound(assignments, FakeScenarios(), rounds)
    first = start.execute(employee(), "module-a")
    for position in range(1, 6):
        first_round = rounds.items[0]
        first_round.answer(position, "right", datetime(2026, 10, 21, tzinfo=ZURICH))
    rounds.items[0].complete(datetime(2026, 10, 21, tzinfo=ZURICH))
    second = start.execute(employee(), "module-a")

    assert second.attempt_number == 2
    assert second.id != first.id


def test_inactive_scenario_is_not_used_for_new_round_but_open_snapshot_is_kept():
    assignments = FakeAssignments()
    rounds = FakeRounds()
    start = StartOrResumeGameRound(assignments, FakeScenariosWithInactive(), rounds)

    with pytest.raises(ValueError):
        start.execute(employee(), "module-a")

    open_round = GameRound.start(
        id="open-round",
        employee_id=employee().id,
        assignment_id="assignment-a",
        attempt_number=1,
        scenarios=scenarios(),
    )
    rounds.items.append(open_round)
    resumed = start.execute(employee(), "module-a")

    assert resumed.id == "open-round"
    assert resumed.scenario_ids == tuple(f"scenario-{number}" for number in range(1, 6))


def test_submit_answer_returns_feedback_and_rejects_foreign_round():
    assignments = FakeAssignments()
    rounds = FakeRounds()
    start = StartOrResumeGameRound(assignments, FakeScenarios(), rounds)
    started = start.execute(employee(), "module-a")
    submit = SubmitRoundAnswer(rounds, FakeClock(datetime(2026, 10, 21, tzinfo=ZURICH)))

    feedback = submit.execute(employee(), started.id, 1, "right")

    assert feedback.correct is True
    assert feedback.next_position == 2

    with pytest.raises(NotFound):
        submit.execute(
            Actor("other", Role.EMPLOYEE, "department-a"), started.id, 2, "right"
        )


def test_department_lead_sees_no_individual_values_before_three_completed_people():
    assignments = FakeAssignments()
    rounds = FakeRounds()
    for number in range(2):
        game_round = GameRound.start(
            id=f"round-{number}",
            employee_id=f"employee-{number}",
            assignment_id="assignment-a",
            attempt_number=1,
            scenarios=scenarios(),
        )
        completed_at = datetime(2026, 10, 20, 10, number, tzinfo=ZURICH)
        for position in range(1, 6):
            game_round.answer(position, "right", completed_at)
        game_round.complete(completed_at)
        rounds.items.append(game_round)

    progress = GetTrainingProgress(
        assignments, rounds, FakeClock(datetime(2026, 10, 21, tzinfo=ZURICH))
    )
    result = progress.execute(
        Actor("lead-1", Role.DEPARTMENT_LEAD, "department-a"), "module-a"
    )

    assert result.aggregate_available is False
    assert result.scores is None


def test_role_specific_progress_visibility():
    """Abteilungsleitung sieht Aggregate ab 3 abgeschlossenen Personen.

    Mitarbeitende sehen nur den eigenen Status.
    """
    assignments = FakeAssignments()
    rounds = FakeRounds()
    for number in range(3):
        game_round = GameRound.start(
            id=f"round-{number}",
            employee_id=f"employee-{number}",
            assignment_id="assignment-a",
            attempt_number=1,
            scenarios=scenarios(),
        )
        completed_at = datetime(2026, 10, 20, 10, number, tzinfo=ZURICH)
        for position in range(1, 6):
            game_round.answer(position, "right", completed_at)
        game_round.complete(completed_at)
        rounds.items.append(game_round)

    progress = GetTrainingProgress(
        assignments, rounds, FakeClock(datetime(2026, 10, 21, tzinfo=ZURICH))
    )
    lead_result = progress.execute(
        Actor("lead-1", Role.DEPARTMENT_LEAD, "department-a"), "module-a"
    )
    employee_result = progress.execute(employee(), "module-a")

    assert lead_result.aggregate_available is True
    assert set(lead_result.scores) == {"completed_people", "total_score"}
    assert lead_result.scores["completed_people"] == 3
    assert employee_result.aggregate_available is False
    assert employee_result.scores == {"best": 5}


def test_data_protection_officer_can_see_other_departments_progress():
    assignments = FakeAssignments()
    rounds = FakeRounds()
    progress = GetTrainingProgress(
        assignments, rounds, FakeClock(datetime(2026, 10, 21, tzinfo=ZURICH))
    )

    result = progress.execute(
        Actor("officer-1", Role.DATA_PROTECTION_OFFICER, "department-a"), "module-b"
    )

    assert result.aggregate_available is False
