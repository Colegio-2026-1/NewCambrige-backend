"""agregar_campos_uniformes

Revision ID: d3f0306084fa
Revises: 8438a9245df3
Create Date: 2026-06-05 01:09:55.653248

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d3f0306084fa"
down_revision: Union[str, None] = "8438a9245df3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Agrega los nuevos campos del módulo de uniformes.
    """



    op.add_column(
        "inventario_objeto",
        sa.Column(
            "estado_fisico",
            sa.String(20),
            nullable=True
        )
    )

    op.add_column(
        "inventario_objeto",
        sa.Column(
            "talla",
            sa.String(10),
            nullable=True
        )
    )

    op.add_column(
        "inventario_objeto",
        sa.Column(
            "observacion",
            sa.Text(),
            nullable=True
        )
    )

    op.add_column(
        "inventario_objeto",
        sa.Column(
            "fecha_registro",
            sa.Date(),
            nullable=True
        )
    )


    op.add_column(
        "prestamo_objeto",
        sa.Column(
            "estado_prestamo",
            sa.String(20),
            nullable=False,
            server_default="prestado"
        )
    )

    op.add_column(
        "prestamo_objeto",
        sa.Column(
            "observacion",
            sa.Text(),
            nullable=True
        )
    )


def downgrade() -> None:

    op.drop_column(
        "prestamo_objeto",
        "observacion"
    )

    op.drop_column(
        "prestamo_objeto",
        "estado_prestamo"
    )

    

    op.drop_column(
        "inventario_objeto",
        "fecha_registro"
    )

    op.drop_column(
        "inventario_objeto",
        "observacion"
    )

    op.drop_column(
        "inventario_objeto",
        "talla"
    )

    op.drop_column(
        "inventario_objeto",
        "estado_fisico"
    )