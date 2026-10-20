"""search v2 data model

Revision ID: b1c2d3e4f5a6
Revises: a3b1c2d4e5f6
Create Date: 2026-10-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a3b1c2d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # -- users --
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('time_zone', sa.String(64), nullable=False, server_default='UTC'),
        )

    # -- criteria --
    with op.batch_alter_table('criteria', schema=None) as batch_op:
        batch_op.add_column(sa.Column('facets_json', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('facets_version', sa.String(16), nullable=True))
        batch_op.add_column(sa.Column('facets_text_sha', sa.String(64), nullable=True))
        batch_op.add_column(
            sa.Column('parsed_at', sa.DateTime(timezone=True), nullable=True),
        )

    # -- events --
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('start_tz', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('end_time', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('source_url', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('page_kind', sa.String(16), nullable=True))
        batch_op.add_column(
            sa.Column('city', sa.String(), nullable=False, server_default=''),
        )
        batch_op.add_column(
            sa.Column('country', sa.String(2), nullable=False, server_default='ZZ'),
        )
        batch_op.add_column(sa.Column('price_amount', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('price_currency', sa.String(3), nullable=True))
        batch_op.add_column(sa.Column('source_query', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('extraction_confidence', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('judge_version', sa.String(16), nullable=True))
        batch_op.alter_column('scorer_model', new_column_name='judge_model')
        batch_op.drop_constraint('uq_event_user_link', type_='unique')
        batch_op.create_unique_constraint(
            'uq_event_user_link_date', ['user_id', 'link', 'date_time'],
        )

    # -- runs --
    with op.batch_alter_table('runs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stage_counts', sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column('search_calls', sa.Integer(), nullable=False, server_default='0'),
        )
        batch_op.add_column(
            sa.Column('llm_calls', sa.Integer(), nullable=False, server_default='0'),
        )
        batch_op.add_column(
            sa.Column('llm_tokens_in', sa.Integer(), nullable=False, server_default='0'),
        )
        batch_op.add_column(
            sa.Column('llm_tokens_out', sa.Integer(), nullable=False, server_default='0'),
        )
        batch_op.add_column(sa.Column('cost_usd', sa.Float(), nullable=True))
        batch_op.add_column(
            sa.Column('stopped_at_stage', sa.String(16), nullable=True),
        )
        batch_op.add_column(sa.Column('error_detail', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # -- runs --
    with op.batch_alter_table('runs', schema=None) as batch_op:
        batch_op.drop_column('error_detail')
        batch_op.drop_column('stopped_at_stage')
        batch_op.drop_column('cost_usd')
        batch_op.drop_column('llm_tokens_out')
        batch_op.drop_column('llm_tokens_in')
        batch_op.drop_column('llm_calls')
        batch_op.drop_column('search_calls')
        batch_op.drop_column('stage_counts')

    # -- events --
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_constraint('uq_event_user_link_date', type_='unique')
        batch_op.create_unique_constraint(
            'uq_event_user_link', ['user_id', 'link'],
        )
        batch_op.alter_column('judge_model', new_column_name='scorer_model')
        batch_op.drop_column('judge_version')
        batch_op.drop_column('extraction_confidence')
        batch_op.drop_column('source_query')
        batch_op.drop_column('price_currency')
        batch_op.drop_column('price_amount')
        batch_op.drop_column('country')
        batch_op.drop_column('city')
        batch_op.drop_column('page_kind')
        batch_op.drop_column('source_url')
        batch_op.drop_column('end_time')
        batch_op.drop_column('start_tz')

    # -- criteria --
    with op.batch_alter_table('criteria', schema=None) as batch_op:
        batch_op.drop_column('parsed_at')
        batch_op.drop_column('facets_text_sha')
        batch_op.drop_column('facets_version')
        batch_op.drop_column('facets_json')

    # -- users --
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('time_zone')
