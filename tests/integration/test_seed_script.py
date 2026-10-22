import importlib.util
from pathlib import Path

from sqlalchemy import create_engine, func, select

import app.infrastructure.models  # noqa: F401
from app.infrastructure.db import Base

SCRIPT = Path(__file__).parents[2] / "scripts" / "seed.py"


def run_seed_script():
    spec = importlib.util.spec_from_file_location("seed_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


def row_counts(engine):
    with engine.connect() as connection:
        return {
            table.name: connection.execute(
                select(func.count()).select_from(table)
            ).scalar_one()
            for table in Base.metadata.sorted_tables
        }


def test_seed_script_can_run_on_every_container_start(tmp_path, monkeypatch):
    # Charakterisierungstest: Render führt den Seed bei jedem Start aus (RUN_SEED).
    database_url = f"sqlite:///{tmp_path / 'seed.db'}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("DEMO_PASSWORD", "demo-password")

    run_seed_script()
    first = row_counts(engine)
    run_seed_script()

    assert first["employees"] > 0
    assert row_counts(engine) == first
