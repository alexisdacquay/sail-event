"""add decided_by to events

Revision ID: a3b1c2d4e5f6
Revises: 8fd52e535cdd
Create Date: 2026-10-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b1c2d4e5f6'
down_revision: Union[str, Sequence[str], None] = '8fd52e535cdd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('decided_by', sa.String(4), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_column('decided_by')
