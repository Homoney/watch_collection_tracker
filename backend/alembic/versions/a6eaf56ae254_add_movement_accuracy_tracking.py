"""Add movement accuracy tracking

Revision ID: a6eaf56ae254
Revises: 708829d09ee0
Create Date: 2026-01-29 16:30:00.038930

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a6eaf56ae254'
down_revision: Union[str, None] = '708829d09ee0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create movement_accuracy_readings table
    op.create_table(
        'movement_accuracy_readings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('watch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('watch_seconds_position', sa.Integer(), nullable=False),
        sa.Column('is_initial_reading', sa.Boolean(), nullable=False),
        sa.Column('is_atomic_source', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('watch_seconds_position IN (0, 15, 30, 45)', name='valid_seconds_position'),
        sa.ForeignKeyConstraint(['watch_id'], ['watches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_movement_accuracy_readings_watch_id'), 'movement_accuracy_readings', ['watch_id'], unique=False)
    op.create_index(op.f('ix_movement_accuracy_readings_reference_time'), 'movement_accuracy_readings', ['reference_time'], unique=False)
    op.create_index(op.f('ix_movement_accuracy_readings_is_initial_reading'), 'movement_accuracy_readings', ['is_initial_reading'], unique=False)

    # Create composite index for pagination
    op.create_index('ix_movement_accuracy_readings_watch_time', 'movement_accuracy_readings', ['watch_id', sa.text('reference_time DESC')], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_movement_accuracy_readings_watch_time', table_name='movement_accuracy_readings')
    op.drop_index(op.f('ix_movement_accuracy_readings_is_initial_reading'), table_name='movement_accuracy_readings')
    op.drop_index(op.f('ix_movement_accuracy_readings_reference_time'), table_name='movement_accuracy_readings')
    op.drop_index(op.f('ix_movement_accuracy_readings_watch_id'), table_name='movement_accuracy_readings')

    # Drop table
    op.drop_table('movement_accuracy_readings')
