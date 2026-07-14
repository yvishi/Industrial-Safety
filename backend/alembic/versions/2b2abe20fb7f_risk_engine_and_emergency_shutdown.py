"""risk engine and emergency shutdown

Adds the Compound Risk Engine's persistent footprint: a manual/external emergency-shutdown
flag on Zone (a stand-in for a future real ESD/DCS integration), and the risk_snapshots table
that stores frozen risk assessments whenever a zone's level changes or its score moves
significantly. Purely additive; existing rows get sensible defaults.

Revision ID: 2b2abe20fb7f
Revises: a4c8e5d21f36
Create Date: 2026-07-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2b2abe20fb7f'
down_revision: Union[str, Sequence[str], None] = 'a4c8e5d21f36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'zones',
        sa.Column('emergency_shutdown_active', sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        'risk_snapshots',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('zone_id', sa.Uuid(as_uuid=True), sa.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Integer(), nullable=False),
        sa.Column('is_emergency_override', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('categories', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('contributors', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('explanation', sa.String(length=2000), nullable=False),
        sa.Column('engine_version', sa.String(length=30), nullable=False),
        sa.Column('trigger_source', sa.String(length=30), nullable=False, server_default='scheduler_tick'),
        sa.Column('evaluation_duration_ms', sa.Integer(), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_risk_snapshots_zone_id'), 'risk_snapshots', ['zone_id'], unique=False)
    op.create_index(op.f('ix_risk_snapshots_level'), 'risk_snapshots', ['level'], unique=False)
    op.create_index(op.f('ix_risk_snapshots_evaluated_at'), 'risk_snapshots', ['evaluated_at'], unique=False)
    op.create_index(
        'ix_risk_snapshots_zone_id_evaluated_at', 'risk_snapshots', ['zone_id', 'evaluated_at'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_risk_snapshots_zone_id_evaluated_at', table_name='risk_snapshots')
    op.drop_index(op.f('ix_risk_snapshots_evaluated_at'), table_name='risk_snapshots')
    op.drop_index(op.f('ix_risk_snapshots_level'), table_name='risk_snapshots')
    op.drop_index(op.f('ix_risk_snapshots_zone_id'), table_name='risk_snapshots')
    op.drop_table('risk_snapshots')
    op.drop_column('zones', 'emergency_shutdown_active')
