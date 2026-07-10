"""plant type, zone category, instrument operating ranges, permit isolation

Adds the configuration-driven Plant Type layer's persistent footprint: which industry a plant
belongs to, coarse zone categories, per-instrument alarm bands + sampling interval, and the
isolation standard on permits. Purely additive; existing rows get sensible defaults.

Revision ID: a4c8e5d21f36
Revises: dcd6c2406a80
Create Date: 2026-07-11 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4c8e5d21f36'
down_revision: Union[str, Sequence[str], None] = 'dcd6c2406a80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'plants',
        sa.Column('plant_type', sa.String(length=40), nullable=False,
                  server_default='crude_oil_refinery'),
    )
    op.create_index(op.f('ix_plants_plant_type'), 'plants', ['plant_type'], unique=False)

    op.add_column(
        'zones',
        sa.Column('zone_category', sa.String(length=40), nullable=False, server_default='process'),
    )
    op.create_index(op.f('ix_zones_zone_category'), 'zones', ['zone_category'], unique=False)

    op.add_column('sensors', sa.Column('normal_min', sa.Float(), nullable=True))
    op.add_column('sensors', sa.Column('normal_max', sa.Float(), nullable=True))
    op.add_column('sensors', sa.Column('warning_min', sa.Float(), nullable=True))
    op.add_column('sensors', sa.Column('warning_max', sa.Float(), nullable=True))
    op.add_column('sensors', sa.Column('critical_min', sa.Float(), nullable=True))
    op.add_column('sensors', sa.Column('critical_max', sa.Float(), nullable=True))
    op.add_column(
        'sensors',
        sa.Column('sampling_interval_seconds', sa.Integer(), nullable=False, server_default='5'),
    )

    op.add_column('permits', sa.Column('required_isolation', sa.String(length=40), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('permits', 'required_isolation')
    op.drop_column('sensors', 'sampling_interval_seconds')
    op.drop_column('sensors', 'critical_max')
    op.drop_column('sensors', 'critical_min')
    op.drop_column('sensors', 'warning_max')
    op.drop_column('sensors', 'warning_min')
    op.drop_column('sensors', 'normal_max')
    op.drop_column('sensors', 'normal_min')
    op.drop_index(op.f('ix_zones_zone_category'), table_name='zones')
    op.drop_column('zones', 'zone_category')
    op.drop_index(op.f('ix_plants_plant_type'), table_name='plants')
    op.drop_column('plants', 'plant_type')
