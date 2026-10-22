from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.models import EvidenceRow
from app.domain.models import Assignment
from app.infrastructure.csv import TrainingEvidenceCsvAdapter
from app.infrastructure.db import Base
from app.infrastructure.repositories import (
    SqlAlchemyAssignmentRepository,
    SqlAlchemyDepartmentRepository,
    SqlAlchemyEmployeeRepository,
    SqlAlchemyModuleRepository,
)
from app.infrastructure.seed import load_seed_data

SEED_DIR = Path(__file__).parents[2] / "data" / "seed"
ZURICH = ZoneInfo("Europe/Zurich")


def database():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_assignment_repository_supports_save_and_employee_lookup():
    engine = database()
    with Session(engine) as session:
        load_seed_data(session, SEED_DIR)
        repository = SqlAlchemyAssignmentRepository(session)
        assignment = repository.save(
            Assignment(
                "assignment-extra",
                "module-einwohnerdienste",
                "department-einwohnerdienste",
                date(2026, 12, 31),
            )
        )
        session.commit()

        assert repository.get(assignment.id) == assignment
        assert assignment.id in {
            item.id for item in repository.for_employee("user-einwohnerdienste-01")
        }


def test_master_data_repositories_provide_display_names():
    engine = database()
    with Session(engine) as session:
        load_seed_data(session, SEED_DIR)
        department = SqlAlchemyDepartmentRepository(session).get(
            "department-einwohnerdienste"
        )
        modules = SqlAlchemyModuleRepository(session).all()

        assert department.name == "Einwohnerdienste"
        assert len(modules) == 3
        assert {module.id: module.name for module in modules}[
            "module-einwohnerdienste"
        ] == "Datenschutz in den Einwohnerdiensten"


def test_master_data_repositories_load_seed_entities():
    engine = database()
    with Session(engine) as session:
        load_seed_data(session, SEED_DIR)
        assert (
            SqlAlchemyEmployeeRepository(session).get("user-einwohnerdienste-01")
            is not None
        )
        assert (
            SqlAlchemyDepartmentRepository(session).get("department-einwohnerdienste")
            is not None
        )
        assert (
            SqlAlchemyModuleRepository(session).get("module-einwohnerdienste")
            is not None
        )


def test_csv_adapter_uses_requested_evidence_format():
    csv = TrainingEvidenceCsvAdapter().render(
        (
            EvidenceRow(
                person="Marek Dalenor",
                department="Einwohnerdienste",
                module="Datenschutz am Schalter",
                attempt_number=1,
                status="abgeschlossen",
                score=3,
                passed=False,
                completed_at=datetime(2026, 10, 21, 14, 5, tzinfo=ZURICH),
                scenario_ids=("scenario-1", "scenario-2"),
                scenario_titles=("Adresse ändern", "Auskunft am Telefon"),
            ),
            EvidenceRow(
                person="Marek Dalenor",
                department="Einwohnerdienste",
                module="Datenschutz am Schalter",
                attempt_number=2,
                status="offen",
                score=None,
                passed=None,
                completed_at=None,
                scenario_ids=("scenario-3",),
            ),
        )
    )

    expected = (
        "\ufeffPerson;Abteilung;Modul;Versuch;Status;Punktzahl;Bestanden;"
        "Abgeschlossen am;Szenarien\r\n"
        "Marek Dalenor;Einwohnerdienste;Datenschutz am Schalter;1;abgeschlossen;"
        "3;nein;21.10.2026 14:05;Adresse ändern|Auskunft am Telefon\r\n"
        "Marek Dalenor;Einwohnerdienste;Datenschutz am Schalter;2;offen;"
        ";;;scenario-3\r\n"
    )
    assert csv == expected
