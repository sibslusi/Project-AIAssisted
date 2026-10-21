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
    status: str | None = None


@dataclass(frozen=True)
class EmployeeRecord:
    id: str
    department_id: str
    first_name: str = ""
    last_name: str = ""


@dataclass(frozen=True)
class PersonalStatus:
    assignment_id: str
    module_id: str
    status: str
    score: int | None


@dataclass(frozen=True)
class PersonStatus:
    employee_id: str
    status: str
    assignment_id: str | None = None
    module_id: str | None = None


@dataclass(frozen=True)
class DepartmentStatus:
    department_id: str
    persons: tuple[PersonStatus, ...]


@dataclass(frozen=True)
class TeamAggregationView:
    department_id: str
    assignment_id: str
    module_id: str
    available: bool
    message: str | None
    participant_count: int
    total_score: int | None
    total_errors: int | None


@dataclass(frozen=True)
class OverallEvaluation:
    departments: tuple[DepartmentStatus, ...]


@dataclass(frozen=True)
class ModuleRecord:
    id: str


@dataclass(frozen=True)
class DepartmentRecord:
    id: str
