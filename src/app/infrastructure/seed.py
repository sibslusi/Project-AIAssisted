import json
import os
from datetime import date
from pathlib import Path

from argon2 import PasswordHasher
from sqlalchemy.orm import Session

from app.infrastructure.models import (
    AssignmentModel,
    DepartmentModel,
    EmployeeModel,
    ModuleModel,
    ModuleScenarioModel,
    ScenarioModel,
)


def _read(seed_dir: Path, name: str):
    return json.loads((seed_dir / name).read_text(encoding="utf-8"))


def load_seed_data(session: Session, seed_dir: Path) -> None:
    password = os.environ.get("DEMO_PASSWORD")
    if not password:
        raise RuntimeError("DEMO_PASSWORD muss gesetzt sein")
    for item in _read(seed_dir, "departments.json"):
        session.merge(DepartmentModel(**item))
    for item in _read(seed_dir, "modules.json"):
        scenario_ids = item.pop("scenario_ids")
        session.merge(ModuleModel(**item))
        for position, scenario_id in enumerate(scenario_ids, 1):
            session.merge(
                ModuleScenarioModel(
                    module_id=item["id"], position=position, scenario_id=scenario_id
                )
            )
    for item in _read(seed_dir, "scenarios.json"):
        session.merge(ScenarioModel(**item))
    for item in _read(seed_dir, "assignments.json"):
        item["due_date"] = date.fromisoformat(item["due_date"])
        session.merge(AssignmentModel(**item))
    hasher = PasswordHasher()
    password_hash = hasher.hash(password)
    for item in _read(seed_dir, "users.json"):
        session.merge(EmployeeModel(**item, password_hash=password_hash))
    session.flush()
