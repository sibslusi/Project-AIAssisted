from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db import Base


class DepartmentModel(Base):
    __tablename__ = "departments"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))


class EmployeeModel(Base):
    __tablename__ = "employees"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    role: Mapped[str] = mapped_column(String(50))
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.id"))
    password_hash: Mapped[str] = mapped_column(String(255))


class ModuleModel(Base):
    __tablename__ = "modules"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))


class ScenarioModel(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    situation: Mapped[str] = mapped_column(String(4000))
    explanation: Mapped[str] = mapped_column(String(4000))
    legal_basis: Mapped[str] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean)
    options: Mapped[list[dict]] = mapped_column(JSON)


class ModuleScenarioModel(Base):
    __tablename__ = "module_scenarios"
    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))


class AssignmentModel(Base):
    __tablename__ = "assignments"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id"))
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.id"))
    due_date: Mapped[date] = mapped_column(Date)


class GameRoundModel(Base):
    __tablename__ = "game_rounds"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"))
    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.id"))
    attempt_number: Mapped[int] = mapped_column(Integer)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score: Mapped[int | None] = mapped_column(Integer)
    passed: Mapped[bool | None] = mapped_column(Boolean)


class GameRoundScenarioModel(Base):
    __tablename__ = "game_round_scenarios"
    round_id: Mapped[str] = mapped_column(
        ForeignKey("game_rounds.id"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))


class RoundAnswerModel(Base):
    __tablename__ = "round_answers"
    round_id: Mapped[str] = mapped_column(
        ForeignKey("game_rounds.id"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    option_id: Mapped[str] = mapped_column(String(100))
    correct: Mapped[bool] = mapped_column(Boolean)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
