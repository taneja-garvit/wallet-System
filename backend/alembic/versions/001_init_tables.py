"""Initial migration - create users, wallets, and transactions tables

Revision ID: 001_init_tables
Revises: 
Create Date: 2026-01-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_init_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create wallets table
    op.create_table(
        'wallets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('balance', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_wallet_user_id')
    )

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('idempotency_key', sa.String(), nullable=False),
        sa.Column('sender_wallet_id', sa.Integer(), nullable=False),
        sa.Column('receiver_wallet_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sender_wallet_id'], ['wallets.id'], ),
        sa.ForeignKeyConstraint(['receiver_wallet_id'], ['wallets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transactions_idempotency_key', 'transactions', ['idempotency_key'], unique=True)
    op.create_index('ix_transactions_created_at', 'transactions', ['created_at'])
    op.create_index('idx_sender_created', 'transactions', ['sender_wallet_id', 'created_at', 'id'])
    op.create_index('idx_receiver_created', 'transactions', ['receiver_wallet_id', 'created_at', 'id'])


def downgrade():
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_index('idx_receiver_created', table_name='transactions')
    op.drop_index('idx_sender_created', table_name='transactions')
    op.drop_index('ix_transactions_created_at', table_name='transactions')
    op.drop_index('ix_transactions_idempotency_key', table_name='transactions')
    op.drop_table('transactions')
    op.drop_table('wallets')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
