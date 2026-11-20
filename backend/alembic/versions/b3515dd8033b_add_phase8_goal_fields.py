"""add_phase8_goal_fields

Revision ID: b3515dd8033b
Revises: d03d0ffba6f1
Create Date: 2026-10-21 19:13:31.145773

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3515dd8033b'
down_revision: Union[str, Sequence[str], None] = 'd03d0ffba6f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('investment_goals', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), server_default='in_progress', nullable=False))
        batch_op.add_column(sa.Column('current_amount', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('initial_lump_sum', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('expected_annual_return', sa.Numeric(precision=6, scale=4), nullable=True))
        batch_op.add_column(sa.Column('monthly_contribution', sa.Numeric(precision=18, scale=2), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('investment_goals', schema=None) as batch_op:
        batch_op.drop_column('monthly_contribution')
        batch_op.drop_column('expected_annual_return')
        batch_op.drop_column('initial_lump_sum')
        batch_op.drop_column('current_amount')
        batch_op.drop_column('status')
