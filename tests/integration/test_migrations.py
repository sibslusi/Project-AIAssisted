import os
import subprocess
import sys

from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_head_creates_all_tables(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'migration.sqlite3'}"
    environment = {**os.environ, "DATABASE_URL": database_url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    engine = create_engine(database_url)
    assert set(inspect(engine).get_table_names()) >= {
        "departments",
        "employees",
        "modules",
        "scenarios",
        "module_scenarios",
        "assignments",
        "game_rounds",
        "game_round_scenarios",
        "round_answers",
    }


def test_alembic_metadata_matches_migrations(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'check.sqlite3'}"
    environment = {**os.environ, "DATABASE_URL": database_url}
    for command in (["upgrade", "head"], ["check"]):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *command],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        assert result.returncode == 0, result.stdout + result.stderr
