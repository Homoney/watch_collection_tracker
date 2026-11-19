"""One primary image per watch (#206).

Older versions could leave a watch with two primary images (the removed
"Fetch images" button, and unsetting a non-primary image). This repairs the
data, then adds a unique index so it cannot happen again:

- a watch with several primary images keeps the first one by sort_order
  (then upload time); the others stop being primary;
- a watch with images but no primary gets its first image as primary;
- a watch whose images share a sort_order gets them renumbered 0, 1, 2...
  in their current order.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-19 21:00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX = "uq_watch_images_one_primary"


def _repair(conn) -> None:
    rows = conn.execute(
        sa.text(
            "SELECT id, watch_id, is_primary, sort_order FROM watch_images "
            "ORDER BY watch_id, sort_order, created_at, id"
        )
    ).fetchall()
    by_watch = {}
    for row in rows:
        by_watch.setdefault(row.watch_id, []).append(row)

    for images in by_watch.values():
        primaries = [r for r in images if r.is_primary]
        keep = primaries[0] if primaries else images[0]
        for r in images:
            want = r.id == keep.id
            if bool(r.is_primary) != want:
                conn.execute(
                    sa.text("UPDATE watch_images SET is_primary = :p WHERE id = :id"),
                    {"p": want, "id": r.id},
                )
        orders = [r.sort_order for r in images]
        if None in orders or len(set(orders)) != len(orders):
            for n, r in enumerate(images):
                if r.sort_order != n:
                    conn.execute(
                        sa.text(
                            "UPDATE watch_images SET sort_order = :n WHERE id = :id"
                        ),
                        {"n": n, "id": r.id},
                    )


def upgrade() -> None:
    _repair(op.get_bind())
    op.create_index(
        INDEX,
        "watch_images",
        ["watch_id"],
        unique=True,
        sqlite_where=sa.text("is_primary = 1"),
        postgresql_where=sa.text("is_primary"),
    )


def downgrade() -> None:
    op.drop_index(INDEX, table_name="watch_images")
