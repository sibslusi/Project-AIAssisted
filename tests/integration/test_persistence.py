import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.domain.models import AnswerOption, GameRound, Scenario
from app.infrastructure.db import Base
from app.infrastructure.models import EmployeeModel
from app.infrastructure.repositories import (
    SqlAlchemyAssignmentRepository,
    SqlAlchemyGameRoundRepository,
    SqlAlchemyScenarioRepository,
)
from app.infrastructure.seed import load_seed_data


SEED_DIR = Path(__file__).parents[2] / "data" / "seed"
ZURICH = ZoneInfo("Europe/Zurich")


def database():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_seed_loader_loads_assignments_and_argon2_password_hashes(monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "demo-only-password")
    engine = database()

    with Session(engine) as session:
        load_seed_data(session, SEED_DIR)
        assignment_repo = SqlAlchemyAssignmentRepository(session)
        assignments = assignment_repo.for_department("department-einwohnerdienste")
        employee = session.scalar(
            select(EmployeeModel).where(EmployeeModel.email == "marek.dalenor@grenchen.example")
        )

    assert len(assignments) == 1
    assert assignments[0].module_id == "module-einwohnerdienste"
    assert assignments[0].due_date == date(2026, 11, 30)
    assert employee is not None
    assert employee.password_hash.startswith("$argon2")


def test_scenario_repository_returns_only_active_scenarios_in_module_order():
    engine = database()
    with Session(engine) as session:
        load_seed_data(session, SEED_DIR)
        repository = SqlAlchemyScenarioRepository(session)
        active = repository.for_module("module-einwohnerdienste")

    assert [scenario.id for scenario in active] == [
        "scenario-einwohnerdienste-01",
        "scenario-einwohnerdienste-02",
        "scenario-einwohnerdienste-03",
        "scenario-einwohnerdienste-04",
        "scenario-einwohnerdienste-05",
    ]


def test_game_round_repository_persists_snapshot_and_answers():
    engine = database()
    scenarios = tuple(
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
    game_round = GameRound.start(
        id="round-1",
        employee_id="user-einwohnerdienste-01",
        assignment_id="assignment-einwohnerdienste",
        attempt_number=1,
        scenarios=scenarios,
    )
    answered_at = datetime(2026, 10, 21, 10, tzinfo=ZURICH)
    game_round.answer(1, "right", answered_at)

    with Session(engine) as session:
        load_seed_data(session, SEED_DIR)
        repository = SqlAlchemyGameRoundRepository(session)
        repository.save(game_round)
        session.commit()
        loaded = repository.get("round-1")

    assert loaded is not None
    assert tuple(scenario.id for scenario in loaded.scenarios) == tuple(
        scenario.id for scenario in scenarios
    )
    assert loaded.answers[1].option_id == "right"
