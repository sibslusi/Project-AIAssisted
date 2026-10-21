"""create UC-001 tables

Revision ID: 0001_initial_uc001
Revises:
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_uc001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
    )
    op.create_table(
        "employees",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column(
            "department_id",
            sa.String(100),
            sa.ForeignKey("departments.id"),
            nullable=False,
        ),
        sa.Column("password_hash", sa.String(255), nullable=False),
    )
    op.create_table(
        "modules",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
    )
    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("situation", sa.String(4000), nullable=False),
        sa.Column("explanation", sa.String(4000), nullable=False),
        sa.Column("legal_basis", sa.String(500), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
    )
    op.create_table(
        "module_scenarios",
        sa.Column(
            "module_id", sa.String(100), sa.ForeignKey("modules.id"), primary_key=True
        ),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column(
            "scenario_id", sa.String(100), sa.ForeignKey("scenarios.id"), nullable=False
        ),
    )
    op.create_table(
        "assignments",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "module_id", sa.String(100), sa.ForeignKey("modules.id"), nullable=False
        ),
        sa.Column(
            "department_id",
            sa.String(100),
            sa.ForeignKey("departments.id"),
            nullable=False,
        ),
        sa.Column("due_date", sa.Date(), nullable=False),
    )
    op.create_table(
        "game_rounds",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "employee_id", sa.String(100), sa.ForeignKey("employees.id"), nullable=False
        ),
        sa.Column(
            "assignment_id",
            sa.String(100),
            sa.ForeignKey("assignments.id"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("score", sa.Integer()),
        sa.Column("passed", sa.Boolean()),
    )
    op.create_table(
        "game_round_scenarios",
        sa.Column(
            "round_id",
            sa.String(100),
            sa.ForeignKey("game_rounds.id"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column(
            "scenario_id", sa.String(100), sa.ForeignKey("scenarios.id"), nullable=False
        ),
    )
    op.create_table(
        "round_answers",
        sa.Column(
            "round_id",
            sa.String(100),
            sa.ForeignKey("game_rounds.id"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("option_id", sa.String(100), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("round_answers")
    op.drop_table("game_round_scenarios")
    op.drop_table("game_rounds")
    op.drop_table("assignments")
    op.drop_table("module_scenarios")
    op.drop_table("scenarios")
    op.drop_table("modules")
    op.drop_table("employees")
    op.drop_table("departments")
