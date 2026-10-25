"""reject stored accepted/queued events that have no start time

Owner decision 2026-10-25 (F). Events stored before the six-field rule
(PR #138) can have a date-only date_time (no "T") and sit in users'
calendars as all-day entries. They become rejected; no row is deleted;
decided_by is left as is.

Downgrade puts every row carrying the cleanup reason back to queued (the
previous accepted/queued status is not kept): they return to the review
queue, not the calendar, and the judge's previous reason stays replaced.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-10-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5a6b7c8d9e0'
down_revision: Union[str, None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

REASON = "No start time (cleanup 2026-10-25)"


def upgrade() -> None:
    op.execute(sa.text(
        "UPDATE events SET status = 'rejected', score_reason = :reason"
        " WHERE status IN ('accepted', 'queued') AND date_time NOT LIKE '%T%'"
    ).bindparams(reason=REASON))


def downgrade() -> None:
    op.execute(sa.text(
        "UPDATE events SET status = 'queued' WHERE status = 'rejected' AND score_reason = :reason"
    ).bindparams(reason=REASON))
