"""event plumbing for operational timeline

Phase 0 of the Operational Timeline / Incident Manager architecture (see
operational-timeline-architecture.md): the two causal edges and the actor/severity tagging
Events need before an Incident entity can exist. incident_id itself is deliberately NOT added
here — the incidents table doesn't exist yet (see the following migration); everything in this
one only depends on tables that already do.

- events.risk_snapshot_id: links a risk_level_increased/decreased event back to the specific
  frozen RiskSnapshot that produced it.
- events.actor_type / actor_id: distinguishes "the engine detected this" from "a person did
  this". Existing rows default to 'system' (every emitter before this migration was internal).
- events.severity: derived server-side from event_type (see EventRepository.create /
  simulation/events.py::make_event), never supplied by a caller. Existing rows backfill to
  'info' since there's no single correct historical value to recompute from event_type at
  migration time; new rows always get a real value from the application.
- recommendations.triggering_snapshot_id: links a Recommendation to whichever RiskSnapshot was
  the "nearest known" frozen assessment when it was created (CRE only persists on meaningful
  change, so this isn't necessarily the exact same tick).

Revision ID: a49d5509a109
Revises: 347e518cce2b
Create Date: 2026-07-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a49d5509a109'
down_revision: Union[str, Sequence[str], None] = '347e518cce2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('events', sa.Column('risk_snapshot_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_events_risk_snapshot_id'), 'events', ['risk_snapshot_id'], unique=False)
    op.create_foreign_key(None, 'events', 'risk_snapshots', ['risk_snapshot_id'], ['id'])

    op.add_column('events', sa.Column('actor_type', sa.String(length=20), nullable=False, server_default='system'))
    op.add_column('events', sa.Column('actor_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_events_actor_id'), 'events', ['actor_id'], unique=False)
    op.create_foreign_key(None, 'events', 'workers', ['actor_id'], ['id'])

    op.add_column('events', sa.Column('severity', sa.String(length=20), nullable=False, server_default='info'))
    op.create_index(op.f('ix_events_severity'), 'events', ['severity'], unique=False)

    op.add_column('recommendations', sa.Column('triggering_snapshot_id', sa.Uuid(), nullable=True))
    op.create_index(
        op.f('ix_recommendations_triggering_snapshot_id'), 'recommendations', ['triggering_snapshot_id'], unique=False
    )
    op.create_foreign_key(None, 'recommendations', 'risk_snapshots', ['triggering_snapshot_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'recommendations', type_='foreignkey')
    op.drop_index(op.f('ix_recommendations_triggering_snapshot_id'), table_name='recommendations')
    op.drop_column('recommendations', 'triggering_snapshot_id')

    op.drop_index(op.f('ix_events_severity'), table_name='events')
    op.drop_column('events', 'severity')

    op.drop_constraint(None, 'events', type_='foreignkey')
    op.drop_index(op.f('ix_events_actor_id'), table_name='events')
    op.drop_column('events', 'actor_id')
    op.drop_column('events', 'actor_type')

    op.drop_constraint(None, 'events', type_='foreignkey')
    op.drop_index(op.f('ix_events_risk_snapshot_id'), table_name='events')
    op.drop_column('events', 'risk_snapshot_id')
