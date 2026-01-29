"""add_performance_indexes

Revision ID: 84f44e7a8266
Revises: 004
Create Date: 2026-01-28 22:01:49.919563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84f44e7a8266'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Watch indexes for filtering and searching
    op.create_index('ix_watches_brand_id', 'watches', ['brand_id'])
    op.create_index('ix_watches_condition', 'watches', ['condition'])
    op.create_index('ix_watches_purchase_date', 'watches', ['purchase_date'])
    op.create_index('ix_watches_collection_id', 'watches', ['collection_id'])
    op.create_index('ix_watches_movement_type_id', 'watches', ['movement_type_id'])

    # Full-text search index on model field (PostgreSQL)
    op.execute("""
        CREATE INDEX ix_watches_model_search
        ON watches USING gin(to_tsvector('english', model))
    """)

    # Service history indexes (watch_id index already exists in initial schema)
    op.create_index('ix_service_history_service_date', 'service_history', ['service_date'])

    # Market value indexes (watch_id and recorded_at indexes already exist in initial schema)

    # Watch image indexes (watch_id index already exists in initial schema)
    op.create_index('ix_watch_images_is_primary', 'watch_images', ['is_primary'])


def downgrade() -> None:
    # Drop indexes in reverse order (only those created in this migration)
    op.drop_index('ix_watch_images_is_primary', table_name='watch_images')
    op.drop_index('ix_service_history_service_date', table_name='service_history')
    op.drop_index('ix_watches_model_search', table_name='watches')
    op.drop_index('ix_watches_movement_type_id', table_name='watches')
    op.drop_index('ix_watches_collection_id', table_name='watches')
    op.drop_index('ix_watches_purchase_date', table_name='watches')
    op.drop_index('ix_watches_condition', table_name='watches')
    op.drop_index('ix_watches_brand_id', table_name='watches')
