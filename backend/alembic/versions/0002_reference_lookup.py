"""Reference look-up: caliber, crystal, case material, look-up cache,
reference photos (image source and source URL).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-18 22:30:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_SOURCES = ("user_upload", "google_images", "url_import")
NEW_SOURCES = OLD_SOURCES + ("reference_photo",)


def upgrade() -> None:
    with op.batch_alter_table("watches") as batch:
        batch.add_column(sa.Column("caliber", sa.String(length=100), nullable=True))
        batch.add_column(sa.Column("crystal", sa.String(length=100), nullable=True))
        batch.add_column(
            sa.Column("case_material", sa.String(length=200), nullable=True)
        )

    with op.batch_alter_table("watch_images") as batch:
        batch.add_column(sa.Column("source_url", sa.String(length=500), nullable=True))
        batch.alter_column(
            "source",
            existing_type=sa.Enum(*OLD_SOURCES, name="imagesourceenum"),
            type_=sa.Enum(*NEW_SOURCES, name="imagesourceenum"),
            existing_nullable=False,
        )

    op.create_table(
        "spec_lookup_cache",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("lookup_key", sa.String(length=200), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "lookup_key"),
    )


def downgrade() -> None:
    op.drop_table("spec_lookup_cache")
    with op.batch_alter_table("watch_images") as batch:
        batch.alter_column(
            "source",
            existing_type=sa.Enum(*NEW_SOURCES, name="imagesourceenum"),
            type_=sa.Enum(*OLD_SOURCES, name="imagesourceenum"),
            existing_nullable=False,
        )
        batch.drop_column("source_url")
    with op.batch_alter_table("watches") as batch:
        batch.drop_column("case_material")
        batch.drop_column("crystal")
        batch.drop_column("caliber")
