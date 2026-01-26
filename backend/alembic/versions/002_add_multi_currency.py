"""Add multi-currency support to wallets and transactions

Revision ID: 002_add_multi_currency
Revises: 001_init_tables
Create Date: 2026-01-26

Changes:
- Add currency column to wallets
- Update wallets unique constraint to (user_id, currency)
- Add FX fields to transactions (source_currency, target_currency, fx_rate, etc.)
- Rename transactions.amount to source_amount
- Add target_amount to transactions
- Add FX metadata columns for audit trail
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_multi_currency'
down_revision = '001_init_tables'
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade to multi-currency support.
    
    Strategy:
    1. Add new columns to wallets and transactions
    2. Migrate existing data (set default currency to USD)
    3. Drop old constraints and add new ones
    """
    
    # --- WALLETS TABLE CHANGES ---
    
    # Add currency column to wallets (default to USD for existing records)
    op.add_column('wallets', 
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD')
    )
    
    # Remove old unique constraint on user_id
    op.drop_constraint('uq_wallet_user_id', 'wallets', type_='unique')
    
    # Add new unique constraint on (user_id, currency)
    op.create_unique_constraint('uq_wallet_user_currency', 'wallets', ['user_id', 'currency'])
    
    # Add index on user_id for fast lookup
    op.create_index('idx_wallet_user_id', 'wallets', ['user_id'])
    
    # Remove server default after migration (enforce explicit currency)
    op.alter_column('wallets', 'currency', server_default=None)
    
    
    # --- TRANSACTIONS TABLE CHANGES ---
    
    # Add source currency and amount (migrate existing amount to source_amount)
    op.add_column('transactions',
        sa.Column('source_currency', sa.String(length=3), nullable=False, server_default='USD')
    )
    op.add_column('transactions',
        sa.Column('source_amount', sa.Numeric(precision=10, scale=2), nullable=True)
    )
    
    # Migrate data: copy amount to source_amount
    op.execute('UPDATE transactions SET source_amount = amount')
    
    # Make source_amount non-nullable after migration
    op.alter_column('transactions', 'source_amount', nullable=False)
    
    # Add target currency and amount
    op.add_column('transactions',
        sa.Column('target_currency', sa.String(length=3), nullable=False, server_default='USD')
    )
    op.add_column('transactions',
        sa.Column('target_amount', sa.Numeric(precision=10, scale=2), nullable=True)
    )
    
    # Migrate data: copy amount to target_amount (same currency = same amount)
    op.execute('UPDATE transactions SET target_amount = amount')
    
    # Make target_amount non-nullable after migration
    op.alter_column('transactions', 'target_amount', nullable=False)
    
    # Add FX metadata
    op.add_column('transactions',
        sa.Column('fx_rate', sa.Numeric(precision=20, scale=10), nullable=False, server_default='1.0')
    )
    op.add_column('transactions',
        sa.Column('fx_provider', sa.String(length=50), nullable=False, server_default='STATIC')
    )
    op.add_column('transactions',
        sa.Column('fx_timestamp', sa.DateTime(), nullable=True)
    )
    
    # Migrate data: set fx_timestamp to created_at for existing records
    op.execute('UPDATE transactions SET fx_timestamp = created_at')
    
    # Make fx_timestamp non-nullable after migration
    op.alter_column('transactions', 'fx_timestamp', nullable=False)
    
    # Remove server defaults after migration
    op.alter_column('transactions', 'source_currency', server_default=None)
    op.alter_column('transactions', 'target_currency', server_default=None)
    op.alter_column('transactions', 'fx_rate', server_default=None)
    op.alter_column('transactions', 'fx_provider', server_default=None)
    
    # Drop old amount column (data already migrated to source_amount)
    op.drop_column('transactions', 'amount')
    
    # Add FX analytics index
    op.create_index('idx_fx_analytics', 'transactions', ['source_currency', 'target_currency', 'created_at'])


def downgrade():
    """
    Downgrade to single-currency system.
    
    Warning: This will lose multi-currency data!
    """
    
    # --- TRANSACTIONS TABLE CHANGES ---
    
    # Drop FX analytics index
    op.drop_index('idx_fx_analytics', table_name='transactions')
    
    # Re-add amount column
    op.add_column('transactions',
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=True)
    )
    
    # Migrate data: copy source_amount back to amount
    op.execute('UPDATE transactions SET amount = source_amount')
    
    # Make amount non-nullable
    op.alter_column('transactions', 'amount', nullable=False)
    
    # Drop FX metadata columns
    op.drop_column('transactions', 'fx_timestamp')
    op.drop_column('transactions', 'fx_provider')
    op.drop_column('transactions', 'fx_rate')
    op.drop_column('transactions', 'target_amount')
    op.drop_column('transactions', 'target_currency')
    op.drop_column('transactions', 'source_amount')
    op.drop_column('transactions', 'source_currency')
    
    
    # --- WALLETS TABLE CHANGES ---
    
    # Drop index on user_id
    op.drop_index('idx_wallet_user_id', table_name='wallets')
    
    # Drop unique constraint on (user_id, currency)
    op.drop_constraint('uq_wallet_user_currency', 'wallets', type_='unique')
    
    # Re-add unique constraint on user_id
    op.create_unique_constraint('uq_wallet_user_id', 'wallets', ['user_id'])
    
    # Drop currency column
    op.drop_column('wallets', 'currency')
