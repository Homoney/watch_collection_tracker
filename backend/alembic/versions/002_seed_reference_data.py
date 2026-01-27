"""seed reference data

Revision ID: 002
Revises: 001
Create Date: 2024-01-27 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Define tables for seeding
    brands_table = table('brands',
        column('id', UUID),
        column('name', sa.String),
        column('sort_order', sa.Integer)
    )

    movement_types_table = table('movement_types',
        column('id', UUID),
        column('name', sa.String),
        column('sort_order', sa.Integer)
    )

    complications_table = table('complications',
        column('id', UUID),
        column('name', sa.String),
        column('sort_order', sa.Integer)
    )

    # Seed brands
    brands = [
        {'id': uuid.uuid4(), 'name': 'Rolex', 'sort_order': 10},
        {'id': uuid.uuid4(), 'name': 'Omega', 'sort_order': 20},
        {'id': uuid.uuid4(), 'name': 'Seiko', 'sort_order': 30},
        {'id': uuid.uuid4(), 'name': 'Grand Seiko', 'sort_order': 40},
        {'id': uuid.uuid4(), 'name': 'Tudor', 'sort_order': 50},
        {'id': uuid.uuid4(), 'name': 'Cartier', 'sort_order': 60},
        {'id': uuid.uuid4(), 'name': 'Patek Philippe', 'sort_order': 70},
        {'id': uuid.uuid4(), 'name': 'Audemars Piguet', 'sort_order': 80},
        {'id': uuid.uuid4(), 'name': 'Vacheron Constantin', 'sort_order': 90},
        {'id': uuid.uuid4(), 'name': 'A. Lange & Söhne', 'sort_order': 100},
        {'id': uuid.uuid4(), 'name': 'Jaeger-LeCoultre', 'sort_order': 110},
        {'id': uuid.uuid4(), 'name': 'IWC', 'sort_order': 120},
        {'id': uuid.uuid4(), 'name': 'Panerai', 'sort_order': 130},
        {'id': uuid.uuid4(), 'name': 'Breitling', 'sort_order': 140},
        {'id': uuid.uuid4(), 'name': 'TAG Heuer', 'sort_order': 150},
        {'id': uuid.uuid4(), 'name': 'Longines', 'sort_order': 160},
        {'id': uuid.uuid4(), 'name': 'Tissot', 'sort_order': 170},
        {'id': uuid.uuid4(), 'name': 'Citizen', 'sort_order': 180},
        {'id': uuid.uuid4(), 'name': 'Casio', 'sort_order': 190},
        {'id': uuid.uuid4(), 'name': 'Hamilton', 'sort_order': 200},
        {'id': uuid.uuid4(), 'name': 'Oris', 'sort_order': 210},
        {'id': uuid.uuid4(), 'name': 'Zenith', 'sort_order': 220},
        {'id': uuid.uuid4(), 'name': 'Hublot', 'sort_order': 230},
        {'id': uuid.uuid4(), 'name': 'Bell & Ross', 'sort_order': 240},
        {'id': uuid.uuid4(), 'name': 'Other', 'sort_order': 1000},
    ]

    op.bulk_insert(brands_table, brands)

    # Seed movement types
    movement_types = [
        {'id': uuid.uuid4(), 'name': 'Hand-wound', 'sort_order': 10},
        {'id': uuid.uuid4(), 'name': 'Automatic', 'sort_order': 20},
        {'id': uuid.uuid4(), 'name': 'Quartz', 'sort_order': 30},
        {'id': uuid.uuid4(), 'name': 'Spring Drive', 'sort_order': 40},
        {'id': uuid.uuid4(), 'name': 'Solar', 'sort_order': 50},
        {'id': uuid.uuid4(), 'name': 'Kinetic', 'sort_order': 60},
    ]

    op.bulk_insert(movement_types_table, movement_types)

    # Seed complications
    complications = [
        {'id': uuid.uuid4(), 'name': 'Date', 'sort_order': 10},
        {'id': uuid.uuid4(), 'name': 'Day-Date', 'sort_order': 20},
        {'id': uuid.uuid4(), 'name': 'Chronograph', 'sort_order': 30},
        {'id': uuid.uuid4(), 'name': 'GMT', 'sort_order': 40},
        {'id': uuid.uuid4(), 'name': 'Dual Time', 'sort_order': 50},
        {'id': uuid.uuid4(), 'name': 'World Time', 'sort_order': 60},
        {'id': uuid.uuid4(), 'name': 'Moon Phase', 'sort_order': 70},
        {'id': uuid.uuid4(), 'name': 'Power Reserve Indicator', 'sort_order': 80},
        {'id': uuid.uuid4(), 'name': 'Annual Calendar', 'sort_order': 90},
        {'id': uuid.uuid4(), 'name': 'Perpetual Calendar', 'sort_order': 100},
        {'id': uuid.uuid4(), 'name': 'Tourbillon', 'sort_order': 110},
        {'id': uuid.uuid4(), 'name': 'Minute Repeater', 'sort_order': 120},
        {'id': uuid.uuid4(), 'name': 'Alarm', 'sort_order': 130},
        {'id': uuid.uuid4(), 'name': 'Regatta Timer', 'sort_order': 140},
        {'id': uuid.uuid4(), 'name': 'Dive Bezel', 'sort_order': 150},
        {'id': uuid.uuid4(), 'name': 'Tachymeter', 'sort_order': 160},
        {'id': uuid.uuid4(), 'name': 'Small Seconds', 'sort_order': 170},
    ]

    op.bulk_insert(complications_table, complications)


def downgrade() -> None:
    # Clear reference data
    op.execute('DELETE FROM complications')
    op.execute('DELETE FROM movement_types')
    op.execute('DELETE FROM brands')
