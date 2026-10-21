from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.models import Actor, Role
from app.infrastructure.models import EmployeeModel


def authenticate(session: Session, email: str, password: str) -> Actor | None:
    employee = session.scalar(
        select(EmployeeModel).where(EmployeeModel.email == email)
    )
    if employee is None:
        return None
    try:
        PasswordHasher().verify(employee.password_hash, password)
    except VerifyMismatchError:
        return None
    return Actor(employee.id, Role(employee.role), employee.department_id)
