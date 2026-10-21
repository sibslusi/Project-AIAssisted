import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SESSION_SECRET", "test-session-secret")
os.environ.setdefault("DEMO_PASSWORD", "demo-password")


@pytest.fixture(scope="session", autouse=True)
def test_database():
    from sqlalchemy.orm import Session

    from app.infrastructure.seed import load_seed_data
    from app.main import app

    app.state.base_metadata.create_all(app.state.engine)
    with Session(app.state.engine) as session:
        load_seed_data(session, app.state.seed_directory)
        session.commit()
    yield
