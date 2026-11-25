"""--fix occurred_at column to be not null in ingestion error model server default

Revision ID: a4699e2e7899
Revises: 21ce19e5b625
Create Date: 2026-11-04 15:49:09.495939

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4699e2e7899"
down_revision: str | Sequence[str] | None = "21ce19e5b625"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "ingestion_errors",
        "occurred_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "ingestion_errors",
        "occurred_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        server_default=None,
        nullable=True,
    )
