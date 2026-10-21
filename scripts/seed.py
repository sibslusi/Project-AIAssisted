import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.infrastructure.seed import load_seed_data


def required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} muss gesetzt sein")
    return value


def main() -> None:
    database_url = required("DATABASE_URL")
    required("DEMO_PASSWORD")
    kwargs = {}
    if database_url.startswith("sqlite://"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if database_url in ("sqlite://", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool
    engine = create_engine(database_url, **kwargs)
    with Session(engine) as session:
        load_seed_data(session, Path(__file__).parents[1] / "data" / "seed")
        session.commit()


if __name__ == "__main__":
    main()
