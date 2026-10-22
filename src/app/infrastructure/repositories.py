from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.models import DepartmentRecord, EmployeeRecord, ModuleRecord
from app.domain.models import AnswerOption, Assignment, GameRound, RoundAnswer, Scenario
from app.infrastructure.models import (
    AssignmentModel,
    DepartmentModel,
    EmployeeModel,
    GameRoundModel,
    GameRoundScenarioModel,
    ModuleModel,
    ModuleScenarioModel,
    RoundAnswerModel,
    ScenarioModel,
)


def _scenario(model: ScenarioModel) -> Scenario:
    return Scenario.create(
        id=model.id,
        situation=model.situation,
        explanation=model.explanation,
        legal_basis=model.legal_basis,
        active=model.active,
        options=tuple(AnswerOption(**option) for option in model.options),
    )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.astimezone(UTC)


def _from_database(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


class SqlAlchemyAssignmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def for_department(self, department_id: str) -> tuple[Assignment, ...]:
        rows = self.session.scalars(
            select(AssignmentModel)
            .where(AssignmentModel.department_id == department_id)
            .order_by(AssignmentModel.id)
        )
        return tuple(
            Assignment(row.id, row.module_id, row.department_id, row.due_date)
            for row in rows
        )

    def all(self) -> tuple[Assignment, ...]:
        rows = self.session.scalars(
            select(AssignmentModel).order_by(AssignmentModel.id)
        )
        return tuple(
            Assignment(row.id, row.module_id, row.department_id, row.due_date)
            for row in rows
        )

    def get(self, assignment_id: str) -> Assignment | None:
        row = self.session.get(AssignmentModel, assignment_id)
        return (
            None
            if row is None
            else Assignment(row.id, row.module_id, row.department_id, row.due_date)
        )

    def save(self, assignment: Assignment) -> Assignment:
        self.session.merge(
            AssignmentModel(
                id=assignment.id,
                module_id=assignment.module_id,
                department_id=assignment.department_id,
                due_date=assignment.due_date,
            )
        )
        self.session.flush()
        return assignment

    def for_employee(self, employee_id: str) -> tuple[Assignment, ...]:
        rows = self.session.scalars(
            select(AssignmentModel)
            .join(
                EmployeeModel,
                EmployeeModel.department_id == AssignmentModel.department_id,
            )
            .where(EmployeeModel.id == employee_id)
            .order_by(AssignmentModel.id)
        )
        return tuple(
            Assignment(row.id, row.module_id, row.department_id, row.due_date)
            for row in rows
        )


class SqlAlchemyEmployeeRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, employee_id: str) -> EmployeeRecord | None:
        row = self.session.get(EmployeeModel, employee_id)
        return (
            None
            if row is None
            else EmployeeRecord(
                row.id, row.department_id, row.first_name, row.last_name
            )
        )

    def for_department(self, department_id: str) -> tuple[EmployeeRecord, ...]:
        rows = self.session.scalars(
            select(EmployeeModel).where(EmployeeModel.department_id == department_id)
        )
        return tuple(
            EmployeeRecord(row.id, row.department_id, row.first_name, row.last_name)
            for row in rows
        )

    def all(self) -> tuple[EmployeeRecord, ...]:
        return tuple(
            EmployeeRecord(row.id, row.department_id, row.first_name, row.last_name)
            for row in self.session.scalars(select(EmployeeModel))
        )


class SqlAlchemyDepartmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, department_id: str) -> DepartmentRecord | None:
        row = self.session.get(DepartmentModel, department_id)
        return None if row is None else DepartmentRecord(row.id, row.name)

    def all(self) -> tuple[DepartmentRecord, ...]:
        return tuple(
            DepartmentRecord(row.id, row.name)
            for row in self.session.scalars(select(DepartmentModel))
        )


class SqlAlchemyModuleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, module_id: str) -> ModuleRecord | None:
        row = self.session.get(ModuleModel, module_id)
        return None if row is None else ModuleRecord(row.id, row.name)

    def all(self) -> tuple[ModuleRecord, ...]:
        return tuple(
            ModuleRecord(row.id, row.name)
            for row in self.session.scalars(select(ModuleModel))
        )


class SqlAlchemyScenarioRepository:
    def __init__(self, session: Session):
        self.session = session

    def for_module(self, module_id: str) -> tuple[Scenario, ...]:
        rows = self.session.scalars(
            select(ScenarioModel)
            .join(
                ModuleScenarioModel, ModuleScenarioModel.scenario_id == ScenarioModel.id
            )
            .where(
                ModuleScenarioModel.module_id == module_id,
                ScenarioModel.active.is_(True),
            )
            .order_by(ModuleScenarioModel.position)
        )
        return tuple(_scenario(row) for row in rows)


class SqlAlchemyGameRoundRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, round_id: str) -> GameRound | None:
        row = self.session.get(GameRoundModel, round_id)
        return None if row is None else self._to_domain(row)

    def open_for(self, employee_id: str, assignment_id: str) -> GameRound | None:
        row = self.session.scalar(
            select(GameRoundModel).where(
                GameRoundModel.employee_id == employee_id,
                GameRoundModel.assignment_id == assignment_id,
                GameRoundModel.completed_at.is_(None),
            )
        )
        return None if row is None else self._to_domain(row)

    def next_attempt_number(self, employee_id: str, assignment_id: str) -> int:
        maximum = self.session.scalar(
            select(func.max(GameRoundModel.attempt_number)).where(
                GameRoundModel.employee_id == employee_id,
                GameRoundModel.assignment_id == assignment_id,
            )
        )
        return (maximum or 0) + 1

    def save(self, game_round: GameRound) -> None:
        row = self.session.get(GameRoundModel, game_round.id)
        is_new = row is None
        if row is None:
            row = GameRoundModel(
                id=game_round.id,
                employee_id=game_round.employee_id,
                assignment_id=game_round.assignment_id,
                attempt_number=game_round.attempt_number,
            )
            self.session.add(row)
        row.completed_at = _as_utc(game_round.completed_at)
        row.score = game_round.score
        row.passed = game_round.passed
        self.session.query(RoundAnswerModel).filter_by(round_id=game_round.id).delete()
        if is_new:
            for position, scenario in enumerate(game_round.scenarios, 1):
                self.session.add(
                    GameRoundScenarioModel(
                        round_id=game_round.id,
                        position=position,
                        scenario_id=scenario.id,
                    )
                )
        for answer in game_round.answers.values():
            self.session.add(
                RoundAnswerModel(
                    round_id=game_round.id,
                    position=answer.position,
                    option_id=answer.option_id,
                    correct=answer.correct,
                    answered_at=_as_utc(answer.answered_at),
                )
            )
        self.session.flush()

    def for_assignment(self, assignment_id: str) -> tuple[GameRound, ...]:
        rows = self.session.scalars(
            select(GameRoundModel).where(GameRoundModel.assignment_id == assignment_id)
        )
        return tuple(self._to_domain(row) for row in rows)

    def _to_domain(self, row: GameRoundModel) -> GameRound:
        scenario_rows = self.session.scalars(
            select(ScenarioModel)
            .join(
                GameRoundScenarioModel,
                GameRoundScenarioModel.scenario_id == ScenarioModel.id,
            )
            .where(GameRoundScenarioModel.round_id == row.id)
            .order_by(GameRoundScenarioModel.position)
        )
        result = GameRound(
            row.id,
            row.employee_id,
            row.assignment_id,
            row.attempt_number,
            tuple(_scenario(item) for item in scenario_rows),
            completed_at=_from_database(row.completed_at),
            score=row.score,
            passed=row.passed,
        )
        answers = self.session.scalars(
            select(RoundAnswerModel).where(RoundAnswerModel.round_id == row.id)
        )
        result.answers = {
            item.position: RoundAnswer(
                item.position,
                item.option_id,
                item.correct,
                _from_database(item.answered_at),
            )
            for item in answers
        }
        return result
