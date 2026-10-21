from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domain.models import Assignment, EvidenceRecord
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
            EvidenceRecord(
                employee_id="employee-1",
                module_id="module-1",
                completed_at=datetime(2026, 10, 21, 14, 5, tzinfo=ZURICH),
            ),
        )
    )

    expected = (
        "\ufeffPerson;Abteilung;Modul;Abgeschlossen am\r\n"
        "employee-1;;module-1;2026-10-21T14:05:00+02:00\r\n"
    )
    assert csv == expected
