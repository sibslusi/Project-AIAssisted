import os
from pathlib import Path

from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.auth import authenticate
from app.infrastructure.clock import SystemClock
from app.infrastructure.csv import TrainingEvidenceCsvAdapter
from app.infrastructure.db import Base
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
from app.interfaces.web import router as web_router


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
            clock=SystemClock(),
            authenticate=authenticate,
            session_secret=session_secret,
        )
    )
    application.state.engine = engine
    application.state.base_metadata = Base.metadata
    application.state.seed_directory = Path(__file__).parents[2] / "data" / "seed"
    application.include_router(web_router)
    static_directory = Path(__file__).parent / "interfaces" / "static"
    application.mount(
        "/static", StaticFiles(directory=static_directory), name="static"
    )
    return application


app = create_app()
