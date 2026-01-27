"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('default_currency', sa.Enum('USD', 'EUR', 'GBP', 'CHF', name='currencyenum'), nullable=False),
        sa.Column('theme', sa.Enum('light', 'dark', name='themeenum'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create brands table
    op.create_table('brands',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
    )
    op.create_index('ix_brands_name', 'brands', ['name'], unique=True)

    # Create movement_types table
    op.create_table('movement_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
    )
    op.create_index('ix_movement_types_name', 'movement_types', ['name'], unique=True)

    # Create complications table
    op.create_table('complications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
    )
    op.create_index('ix_complications_name', 'complications', ['name'], unique=True)

    # Create collections table
    op.create_table('collections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), server_default='#3B82F6'),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create watches table
    op.create_table('watches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('movement_type_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('reference_number', sa.String(), nullable=True),
        sa.Column('serial_number', sa.String(), nullable=True),
        sa.Column('purchase_date', sa.DateTime(), nullable=True),
        sa.Column('retailer', sa.String(), nullable=True),
        sa.Column('purchase_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('purchase_currency', sa.String(3), server_default='USD'),
        sa.Column('case_diameter', sa.Numeric(5, 2), nullable=True),
        sa.Column('case_thickness', sa.Numeric(5, 2), nullable=True),
        sa.Column('lug_width', sa.Numeric(5, 2), nullable=True),
        sa.Column('water_resistance', sa.Integer(), nullable=True),
        sa.Column('power_reserve', sa.Integer(), nullable=True),
        sa.Column('complications', postgresql.JSONB(astext_type=sa.Text()), server_default='[]'),
        sa.Column('condition', sa.Enum('mint', 'excellent', 'good', 'fair', 'poor', name='conditionenum'), nullable=True),
        sa.Column('current_market_value', sa.Numeric(12, 2), nullable=True),
        sa.Column('current_market_currency', sa.String(3), server_default='USD'),
        sa.Column('last_value_update', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['movement_type_id'], ['movement_types.id'], ondelete='RESTRICT'),
    )
    op.create_index('ix_watches_user_id', 'watches', ['user_id'])

    # Create GIN index for complications JSONB column
    op.execute('CREATE INDEX ix_watches_complications ON watches USING GIN (complications)')

    # Create watch_images table
    op.create_table('watch_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('watch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), server_default='false'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('source', sa.Enum('user_upload', 'google_images', 'url_import', name='imagesourceenum'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['watch_id'], ['watches.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_watch_images_watch_id', 'watch_images', ['watch_id'])

    # Create service_history table
    op.create_table('service_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('watch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_date', sa.DateTime(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('service_type', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('cost_currency', sa.String(3), server_default='USD'),
        sa.Column('next_service_due', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['watch_id'], ['watches.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_service_history_watch_id', 'service_history', ['watch_id'])

    # Create service_documents table
    op.create_table('service_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('service_history_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['service_history_id'], ['service_history.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_service_documents_service_history_id', 'service_documents', ['service_history_id'])

    # Create market_values table
    op.create_table('market_values',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('watch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('value', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD', nullable=False),
        sa.Column('source', sa.Enum('manual', 'chrono24', 'api', name='valuesourceenum'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['watch_id'], ['watches.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_market_values_watch_id', 'market_values', ['watch_id'])
    op.create_index('ix_market_values_recorded_at', 'market_values', ['recorded_at'])


def downgrade() -> None:
    op.drop_table('market_values')
    op.drop_table('service_documents')
    op.drop_table('service_history')
    op.drop_table('watch_images')
    op.drop_table('watches')
    op.drop_table('collections')
    op.drop_table('complications')
    op.drop_table('movement_types')
    op.drop_table('brands')
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS valuesourceenum')
    op.execute('DROP TYPE IF EXISTS imagesourceenum')
    op.execute('DROP TYPE IF EXISTS conditionenum')
    op.execute('DROP TYPE IF EXISTS themeenum')
    op.execute('DROP TYPE IF EXISTS currencyenum')
