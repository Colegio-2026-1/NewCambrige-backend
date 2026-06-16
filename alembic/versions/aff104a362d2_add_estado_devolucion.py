"""add_estado_devolucion

Revision ID: aff104a362d2
Revises: a8ce7a091c9f
Create Date: 2026-06-15 00:28:30.451930
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aff104a362d2'
down_revision: Union[str, None] = 'cc29ff7a61ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "prestamo_objeto",
        sa.Column(
            "estado_devolucion",
            sa.String(length=20),
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column(
        "prestamo_objeto",
        "estado_devolucion"
    )
