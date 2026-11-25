"""index jobs by update time and id

Revision ID: d3b61a2f904e
Revises: a19226e1f6d6
Create Date: 2026-11-25 12:58:25.287000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3b61a2f904e"
down_revision: str | Sequence[str] | None = "a19226e1f6d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_jobs_updated_at_id",
        "jobs",
        ["updated_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_jobs_updated_at_id", table_name="jobs")
