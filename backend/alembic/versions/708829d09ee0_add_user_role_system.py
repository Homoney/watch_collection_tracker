"""Add user role system

Revision ID: 708829d09ee0
Revises: 84f44e7a8266
Create Date: 2026-01-29 15:08:08.253656

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '708829d09ee0'
down_revision: Union[str, None] = '84f44e7a8266'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type first
    userrole_enum = sa.Enum('user', 'admin', name='userrole')
    userrole_enum.create(op.get_bind(), checkfirst=True)

    # Add the column as nullable first with default value
    op.add_column('users', sa.Column('role', userrole_enum, nullable=True))

    # Set default value for existing users (all existing users become regular users)
    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")

    # Make the column non-nullable
    op.alter_column('users', 'role', nullable=False)


def downgrade() -> None:
    # Drop the column
    op.drop_column('users', 'role')

    # Drop the enum type
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
