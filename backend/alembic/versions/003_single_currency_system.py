"""single_currency_system

Revision ID: 003_single_currency
Revises: 002_add_multi_currency
Create Date: 2026-01-26

Simplified to single currency (INR) system.
Changes:
- Removed currency columns from wallets
- Added wallet name field
- Simplified transactions table (removed FX fields)
- One wallet per user

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_single_currency'
down_revision = '002_add_multi_currency'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old tables (we're doing fresh start as user requested)
    op.execute('DROP TABLE IF EXISTS transactions CASCADE')
    op.execute('DROP TABLE IF EXISTS wallets CASCADE')
    # Don't drop users table - keep user data
    
    # Create wallets table (single currency: INR)
    op.create_table(
        'wallets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, server_default='My Wallet'),
        sa.Column('balance', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_wallet_user_id')
    )
    
    # Create transactions table (simplified, single currency)
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
    # Reverse changes (back to multi-currency)
    op.drop_index('idx_receiver_created', table_name='transactions')
    op.drop_index('idx_sender_created', table_name='transactions')
    op.drop_index('ix_transactions_created_at', table_name='transactions')
    op.drop_index('ix_transactions_idempotency_key', table_name='transactions')
    op.drop_table('transactions')
    op.drop_table('wallets')
