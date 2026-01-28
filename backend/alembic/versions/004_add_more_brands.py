"""add more brands

Revision ID: 004
Revises: 003
Create Date: 2026-01-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Define brands table for seeding
    brands_table = table('brands',
        column('id', UUID),
        column('name', sa.String),
        column('sort_order', sa.Integer)
    )

    # Additional brands to add
    # Sort order continues from 240, "Other" remains at 1000
    new_brands = [
        # High-end luxury
        {'id': uuid.uuid4(), 'name': 'Blancpain', 'sort_order': 245},
        {'id': uuid.uuid4(), 'name': 'Glashütte Original', 'sort_order': 250},
        {'id': uuid.uuid4(), 'name': 'Richard Mille', 'sort_order': 255},
        {'id': uuid.uuid4(), 'name': 'MB&F', 'sort_order': 260},
        {'id': uuid.uuid4(), 'name': 'H. Moser & Cie', 'sort_order': 265},
        {'id': uuid.uuid4(), 'name': 'Ulysse Nardin', 'sort_order': 270},
        {'id': uuid.uuid4(), 'name': 'Chopard', 'sort_order': 275},
        {'id': uuid.uuid4(), 'name': 'Piaget', 'sort_order': 280},
        {'id': uuid.uuid4(), 'name': 'Girard-Perregaux', 'sort_order': 285},

        # Mid-range/enthusiast brands
        {'id': uuid.uuid4(), 'name': 'Christopher Ward', 'sort_order': 290},
        {'id': uuid.uuid4(), 'name': 'Sinn', 'sort_order': 295},
        {'id': uuid.uuid4(), 'name': 'Nomos Glashütte', 'sort_order': 300},
        {'id': uuid.uuid4(), 'name': 'Stowa', 'sort_order': 305},
        {'id': uuid.uuid4(), 'name': 'Mido', 'sort_order': 310},
        {'id': uuid.uuid4(), 'name': 'Rado', 'sort_order': 315},
        {'id': uuid.uuid4(), 'name': 'Baume & Mercier', 'sort_order': 320},
        {'id': uuid.uuid4(), 'name': 'Maurice Lacroix', 'sort_order': 325},
        {'id': uuid.uuid4(), 'name': 'Frederique Constant', 'sort_order': 330},
        {'id': uuid.uuid4(), 'name': 'Alpina', 'sort_order': 335},
        {'id': uuid.uuid4(), 'name': 'Montblanc', 'sort_order': 340},

        # Japanese brands
        {'id': uuid.uuid4(), 'name': 'Orient', 'sort_order': 345},
        {'id': uuid.uuid4(), 'name': 'Orient Star', 'sort_order': 350},
        {'id': uuid.uuid4(), 'name': 'Bulova', 'sort_order': 355},
        {'id': uuid.uuid4(), 'name': 'G-Shock', 'sort_order': 360},
        {'id': uuid.uuid4(), 'name': 'Casio Oceanus', 'sort_order': 365},
        {'id': uuid.uuid4(), 'name': 'Citizen Promaster', 'sort_order': 370},

        # Microbrands
        {'id': uuid.uuid4(), 'name': 'Erebus', 'sort_order': 400},
        {'id': uuid.uuid4(), 'name': 'Halios', 'sort_order': 405},
        {'id': uuid.uuid4(), 'name': 'Farer', 'sort_order': 410},
        {'id': uuid.uuid4(), 'name': 'Zelos', 'sort_order': 415},
        {'id': uuid.uuid4(), 'name': 'Nodus', 'sort_order': 420},
        {'id': uuid.uuid4(), 'name': 'Monta', 'sort_order': 425},
        {'id': uuid.uuid4(), 'name': 'Formex', 'sort_order': 430},
        {'id': uuid.uuid4(), 'name': 'Baltic', 'sort_order': 435},
        {'id': uuid.uuid4(), 'name': 'Lorier', 'sort_order': 440},
        {'id': uuid.uuid4(), 'name': 'Vaer', 'sort_order': 445},
        {'id': uuid.uuid4(), 'name': 'Boldr', 'sort_order': 450},
        {'id': uuid.uuid4(), 'name': 'Helm', 'sort_order': 455},
        {'id': uuid.uuid4(), 'name': 'Notice', 'sort_order': 460},
        {'id': uuid.uuid4(), 'name': 'Traska', 'sort_order': 465},
        {'id': uuid.uuid4(), 'name': 'Vertex', 'sort_order': 470},
        {'id': uuid.uuid4(), 'name': 'Anordain', 'sort_order': 475},
        {'id': uuid.uuid4(), 'name': 'Fears', 'sort_order': 480},
        {'id': uuid.uuid4(), 'name': 'Marathon', 'sort_order': 485},
        {'id': uuid.uuid4(), 'name': 'Dan Henry', 'sort_order': 490},
        {'id': uuid.uuid4(), 'name': 'Scurfa', 'sort_order': 495},
        {'id': uuid.uuid4(), 'name': 'Jack Mason', 'sort_order': 500},

        # Aliexpress/Homage brands
        {'id': uuid.uuid4(), 'name': 'Pagani Design', 'sort_order': 600},
        {'id': uuid.uuid4(), 'name': 'San Martin', 'sort_order': 605},
        {'id': uuid.uuid4(), 'name': 'Phylida', 'sort_order': 610},
        {'id': uuid.uuid4(), 'name': 'Steeldive', 'sort_order': 615},
        {'id': uuid.uuid4(), 'name': 'Cronos', 'sort_order': 620},
        {'id': uuid.uuid4(), 'name': 'Heimdallr', 'sort_order': 625},
        {'id': uuid.uuid4(), 'name': 'Addiesdive', 'sort_order': 630},
        {'id': uuid.uuid4(), 'name': 'Escapement Time', 'sort_order': 635},
        {'id': uuid.uuid4(), 'name': 'Baltany', 'sort_order': 640},
        {'id': uuid.uuid4(), 'name': 'Tandorio', 'sort_order': 645},
        {'id': uuid.uuid4(), 'name': 'Bliger', 'sort_order': 650},
        {'id': uuid.uuid4(), 'name': 'Corgeut', 'sort_order': 655},
        {'id': uuid.uuid4(), 'name': 'Parnis', 'sort_order': 660},
        {'id': uuid.uuid4(), 'name': 'Merkur', 'sort_order': 665},

        # Sport/tool watches
        {'id': uuid.uuid4(), 'name': 'Suunto', 'sort_order': 700},
        {'id': uuid.uuid4(), 'name': 'Garmin', 'sort_order': 705},
        {'id': uuid.uuid4(), 'name': 'Luminox', 'sort_order': 710},
        {'id': uuid.uuid4(), 'name': 'Victorinox', 'sort_order': 715},
        {'id': uuid.uuid4(), 'name': 'Wenger', 'sort_order': 720},
        {'id': uuid.uuid4(), 'name': 'Traser', 'sort_order': 725},
        {'id': uuid.uuid4(), 'name': 'Armitron', 'sort_order': 730},

        # Fashion/affordable
        {'id': uuid.uuid4(), 'name': 'Swatch', 'sort_order': 800},
        {'id': uuid.uuid4(), 'name': 'Timex', 'sort_order': 805},
        {'id': uuid.uuid4(), 'name': 'Invicta', 'sort_order': 810},
        {'id': uuid.uuid4(), 'name': 'Fossil', 'sort_order': 815},
        {'id': uuid.uuid4(), 'name': 'Skagen', 'sort_order': 820},
        {'id': uuid.uuid4(), 'name': 'Movado', 'sort_order': 825},
        {'id': uuid.uuid4(), 'name': 'Michael Kors', 'sort_order': 830},
        {'id': uuid.uuid4(), 'name': 'Diesel', 'sort_order': 835},
        {'id': uuid.uuid4(), 'name': 'Nixon', 'sort_order': 840},

        # Vintage/heritage brands
        {'id': uuid.uuid4(), 'name': 'Doxa', 'sort_order': 900},
        {'id': uuid.uuid4(), 'name': 'Squale', 'sort_order': 905},
        {'id': uuid.uuid4(), 'name': 'Certina', 'sort_order': 910},
        {'id': uuid.uuid4(), 'name': 'Eterna', 'sort_order': 915},
        {'id': uuid.uuid4(), 'name': 'Glycine', 'sort_order': 920},
        {'id': uuid.uuid4(), 'name': 'Nivada Grenchen', 'sort_order': 925},
        {'id': uuid.uuid4(), 'name': 'Yema', 'sort_order': 930},
        {'id': uuid.uuid4(), 'name': 'Zodiac', 'sort_order': 935},
    ]

    op.bulk_insert(brands_table, new_brands)


def downgrade() -> None:
    # Delete the newly added brands
    brand_names = [
        'Blancpain', 'Glashütte Original', 'Richard Mille', 'MB&F', 'H. Moser & Cie',
        'Ulysse Nardin', 'Chopard', 'Piaget', 'Girard-Perregaux',
        'Christopher Ward', 'Sinn', 'Nomos Glashütte', 'Stowa', 'Mido', 'Rado',
        'Baume & Mercier', 'Maurice Lacroix', 'Frederique Constant', 'Alpina', 'Montblanc',
        'Orient', 'Orient Star', 'Bulova', 'G-Shock', 'Casio Oceanus', 'Citizen Promaster',
        'Erebus', 'Halios', 'Farer', 'Zelos', 'Nodus', 'Monta', 'Formex', 'Baltic',
        'Lorier', 'Vaer', 'Boldr', 'Helm', 'Notice', 'Traska', 'Vertex', 'Anordain',
        'Fears', 'Marathon', 'Dan Henry', 'Scurfa', 'Jack Mason',
        'Pagani Design', 'San Martin', 'Phylida', 'Steeldive', 'Cronos', 'Heimdallr',
        'Addiesdive', 'Escapement Time', 'Baltany', 'Tandorio', 'Bliger', 'Corgeut',
        'Parnis', 'Merkur',
        'Suunto', 'Garmin', 'Luminox', 'Victorinox', 'Wenger', 'Traser', 'Armitron',
        'Swatch', 'Timex', 'Invicta', 'Fossil', 'Skagen', 'Movado', 'Michael Kors',
        'Diesel', 'Nixon',
        'Doxa', 'Squale', 'Certina', 'Eterna', 'Glycine', 'Nivada Grenchen', 'Yema', 'Zodiac'
    ]

    for brand_name in brand_names:
        op.execute(f"DELETE FROM brands WHERE name = '{brand_name}'")
