from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class Role(StrEnum):
    EMPLOYEE = "employee"
    DEPARTMENT_LEAD = "department_lead"
    DATA_PROTECTION_OFFICER = "data_protection_officer"


@dataclass(frozen=True)
class Actor:
    id: str
    role: Role
    department_id: str


@dataclass(frozen=True)
class Assignment:
    id: str
    module_id: str
    department_id: str
    due_date: date


@dataclass(frozen=True)
class AssignedModule:
    assignment_id: str
    module_id: str
    due_date: date


@dataclass(frozen=True)
class RoundView:
    id: str
    attempt_number: int
    scenario_ids: tuple[str, ...]
    next_position: int | None


@dataclass(frozen=True)
class ProgressView:
    aggregate_available: bool
    scores: dict[str, int] | None
