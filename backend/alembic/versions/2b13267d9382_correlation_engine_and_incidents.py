"""correlation engine and incidents

Phase 1 of the Operational Timeline / Incident Manager architecture (see
operational-timeline-architecture.md): the incidents table — the Correlation Engine's
persisted output — plus the two FK columns that complete the causal chain Sensor -> Rule ->
RiskSnapshot -> Recommendation -> Incident -> Operator Action (events.incident_id,
recommendations.incident_id). recommendations.incident_id replaces what an earlier draft of
this architecture had as a denormalized array on Incident; a real edge instead.

The partial unique index (ux_incidents_primary_zone_id_open) enforces "at most one OPEN
incident per zone" without a second uniqueness table — the same postgresql_where/sqlite_where
pattern that fixed the Recommendation Engine's real recurring-identity_key bug (see
347e518cce2b), scoped here to status='open' instead of a recurring key.

Revision ID: 2b13267d9382
Revises: a49d5509a109
Create Date: 2026-07-16 00:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2b13267d9382'
down_revision: Union[str, Sequence[str], None] = 'a49d5509a109'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'incidents',
        sa.Column('primary_zone_id', sa.Uuid(), nullable=False),
        sa.Column(
            'affected_zone_ids',
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'),
            nullable=False,
        ),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('origin', sa.String(length=20), nullable=False),
        sa.Column('classification', sa.String(length=30), nullable=False),
        sa.Column('risk_severity_at_open', sa.String(length=20), nullable=True),
        sa.Column('peak_risk_severity', sa.String(length=20), nullable=True),
        sa.Column('incident_severity', sa.String(length=20), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('summary', sa.String(length=2000), nullable=False),
        sa.Column(
            'opened_context_snapshot',
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'),
            nullable=True,
        ),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('root_cause', sa.String(length=2000), nullable=True),
        sa.Column(
            'corrective_actions',
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'),
            nullable=False,
        ),
        sa.Column('opened_by_id', sa.Uuid(), nullable=True),
        sa.Column('closed_by_id', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['primary_zone_id'], ['zones.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['opened_by_id'], ['workers.id']),
        sa.ForeignKeyConstraint(['closed_by_id'], ['workers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_incidents_primary_zone_id'), 'incidents', ['primary_zone_id'], unique=False)
    op.create_index(op.f('ix_incidents_status'), 'incidents', ['status'], unique=False)
    op.create_index(op.f('ix_incidents_origin'), 'incidents', ['origin'], unique=False)
    op.create_index(op.f('ix_incidents_classification'), 'incidents', ['classification'], unique=False)
    op.create_index(op.f('ix_incidents_opened_at'), 'incidents', ['opened_at'], unique=False)
    op.create_index(op.f('ix_incidents_opened_by_id'), 'incidents', ['opened_by_id'], unique=False)
    op.create_index(op.f('ix_incidents_closed_by_id'), 'incidents', ['closed_by_id'], unique=False)
    op.create_index(
        'ux_incidents_primary_zone_id_open',
        'incidents',
        ['primary_zone_id'],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
        sqlite_where=sa.text("status = 'open'"),
    )
    op.create_index(
        'ix_incidents_primary_zone_id_opened_at', 'incidents', ['primary_zone_id', 'opened_at'], unique=False
    )

    op.add_column('events', sa.Column('incident_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_events_incident_id'), 'events', ['incident_id'], unique=False)
    op.create_foreign_key(None, 'events', 'incidents', ['incident_id'], ['id'])

    op.add_column('recommendations', sa.Column('incident_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_recommendations_incident_id'), 'recommendations', ['incident_id'], unique=False)
    op.create_foreign_key(None, 'recommendations', 'incidents', ['incident_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'recommendations', type_='foreignkey')
    op.drop_index(op.f('ix_recommendations_incident_id'), table_name='recommendations')
    op.drop_column('recommendations', 'incident_id')

    op.drop_constraint(None, 'events', type_='foreignkey')
    op.drop_index(op.f('ix_events_incident_id'), table_name='events')
    op.drop_column('events', 'incident_id')

    op.drop_index('ix_incidents_primary_zone_id_opened_at', table_name='incidents')
    op.drop_index(
        'ux_incidents_primary_zone_id_open',
        table_name='incidents',
        postgresql_where=sa.text("status = 'open'"),
        sqlite_where=sa.text("status = 'open'"),
    )
    op.drop_index(op.f('ix_incidents_closed_by_id'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_opened_by_id'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_opened_at'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_classification'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_origin'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_status'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_primary_zone_id'), table_name='incidents')
    op.drop_table('incidents')
