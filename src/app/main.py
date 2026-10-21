import os
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.models import Actor, Role
from app.infrastructure.csv import TrainingEvidenceCsvAdapter
from app.infrastructure.db import Base
from app.infrastructure.models import EmployeeModel
from app.infrastructure.repositories import (
    SqlAlchemyAssignmentRepository,
    SqlAlchemyDepartmentRepository,
    SqlAlchemyEmployeeRepository,
    SqlAlchemyGameRoundRepository,
    SqlAlchemyModuleRepository,
    SqlAlchemyScenarioRepository,
)
from app.interfaces.http import Services
from app.interfaces.http import create_app as create_http_app


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} muss gesetzt sein")
    return value


def create_app():
    database_url = _required("DATABASE_URL")
    session_secret = _required("SESSION_SECRET")
    _required("DEMO_PASSWORD")
    engine_kwargs = {}
    if database_url.startswith("sqlite://"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if database_url in ("sqlite://", "sqlite:///:memory:"):
            engine_kwargs["poolclass"] = StaticPool
    engine = create_engine(database_url, **engine_kwargs)
    factory = sessionmaker(bind=engine)
    hasher = PasswordHasher()

    def authenticate(session: Session, email: str, password: str) -> Actor | None:
        employee = session.scalar(
            select(EmployeeModel).where(EmployeeModel.email == email)
        )
        if employee is None:
            return None
        try:
            hasher.verify(employee.password_hash, password)
        except VerifyMismatchError:
            return None
        return Actor(employee.id, Role(employee.role), employee.department_id)

    application = create_http_app(
        Services(
            session_factory=factory,
            assignment_repository=SqlAlchemyAssignmentRepository,
            scenario_repository=SqlAlchemyScenarioRepository,
            game_round_repository=SqlAlchemyGameRoundRepository,
            employee_repository=SqlAlchemyEmployeeRepository,
            department_repository=SqlAlchemyDepartmentRepository,
            module_repository=SqlAlchemyModuleRepository,
            csv_adapter=TrainingEvidenceCsvAdapter(),
            authenticate=authenticate,
            session_secret=session_secret,
        )
    )
    application.state.engine = engine
    application.state.base_metadata = Base.metadata
    application.state.seed_directory = Path(__file__).parents[2] / "data" / "seed"
    return application


app = create_app()
