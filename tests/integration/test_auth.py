from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.infrastructure.auth import revoke_sessions, session_version
from app.infrastructure.db import Base
from app.infrastructure.seed import load_seed_data

SEED_DIR = Path(__file__).parents[2] / "data" / "seed"


def test_revoking_sessions_increments_version_and_survives_seed():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        load_seed_data(session, SEED_DIR)
        session.commit()
        assert session_version(session, "user-einwohnerdienste-01") == 0

        revoke_sessions(session, "user-einwohnerdienste-01")
        session.commit()
        load_seed_data(session, SEED_DIR)
        session.commit()

        assert session_version(session, "user-einwohnerdienste-01") == 1
        assert session_version(session, "user-unknown") is None
