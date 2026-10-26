from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.models import Actor, Role, normalize_email
from app.infrastructure.models import EmployeeModel


def authenticate(session: Session, email: str, password: str) -> Actor | None:
    employee = session.scalar(
        select(EmployeeModel).where(EmployeeModel.email == normalize_email(email))
    )
    if employee is None:
        return None
    try:
        PasswordHasher().verify(employee.password_hash, password)
    except VerifyMismatchError:
        return None
    return Actor(employee.id, Role(employee.role), employee.department_id)


def session_version(session: Session, employee_id: str) -> int | None:
    employee = session.get(EmployeeModel, employee_id)
    return None if employee is None else employee.session_version


def revoke_sessions(session: Session, employee_id: str) -> None:
    employee = session.get(EmployeeModel, employee_id)
    if employee is not None:
        employee.session_version += 1
