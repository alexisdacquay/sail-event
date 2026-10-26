"""drop unique constraint uq_event_user_link_date on events

Owner decision 2026-10-25: two different events may share a link and start
time (listing pages); duplicates are decided by the model check after storage.

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-10-25 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a6b7c8d9e0f1'
down_revision: Union[str, None] = 'f5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('events') as batch_op:
        batch_op.drop_constraint('uq_event_user_link_date', type_='unique')


def downgrade() -> None:
    # Fails while two rows share (user_id, link, date_time): resolve those rows first.
    with op.batch_alter_table('events') as batch_op:
        batch_op.create_unique_constraint('uq_event_user_link_date', ['user_id', 'link', 'date_time'])
