"""delete stored events that have no start time

Owner decision 2026-10-25 (F, "no rubbish anywhere"). Events stored before
the six-field rule (PR #138) can have a date-only date_time (no "T"); they
sit in users' calendars and lists as all-day entries. Every such event is
deleted, whatever its status. No table has a foreign key to events.
IRREVERSIBLE.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-10-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f5a6b7c8d9e0'
down_revision: Union[str, None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM events WHERE date_time NOT LIKE '%T%'")


def downgrade() -> None:
    pass  # irreversible: deleted events cannot be restored
