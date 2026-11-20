"""add users and user_sessions tables and user_id foreign keys

Revision ID: 853278621de3
Revises: 39d7ef5e66fc
Create Date: 2026-10-21 15:13:54.635098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '853278621de3'
down_revision: Union[str, Sequence[str], None] = '39d7ef5e66fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include users, sessions, and user-scoped foreign keys."""
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replaced_by_hash', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_sessions_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_sessions')),
    )
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_sessions_token_hash'), 'user_sessions', ['token_hash'], unique=True)
    op.create_index(op.f('ix_user_sessions_expires_at'), 'user_sessions', ['expires_at'], unique=False)

    # 3. Add user_id column & foreign key to financial_profiles (using batch mode for SQLite compatibility)
    with op.batch_alter_table('financial_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=36), nullable=True))
        batch_op.create_index(batch_op.f('ix_financial_profiles_user_id'), ['user_id'], unique=True)
        batch_op.create_foreign_key(batch_op.f('fk_financial_profiles_user_id_users'), 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # 4. Add user_id column & foreign key to transactions (using batch mode for SQLite compatibility)
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=36), nullable=True))
        batch_op.create_index('idx_transactions_user_date', ['user_id', 'date'], unique=False)
        batch_op.create_index(batch_op.f('ix_transactions_user_id'), ['user_id'], unique=False)
        batch_op.create_foreign_key(batch_op.f('fk_transactions_user_id_users'), 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_transactions_user_id_users'), type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_transactions_user_id'))
        batch_op.drop_index('idx_transactions_user_date')
        batch_op.drop_column('user_id')

    with op.batch_alter_table('financial_profiles', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_financial_profiles_user_id_users'), type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_financial_profiles_user_id'))
        batch_op.drop_column('user_id')

    op.drop_index(op.f('ix_user_sessions_expires_at'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_token_hash'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_user_id'), table_name='user_sessions')
    op.drop_table('user_sessions')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
