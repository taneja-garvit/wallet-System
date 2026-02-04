"""update_default_balance

Revision ID: 004_default_balance
Revises: 003_single_currency
Create Date: 2026-01-26

Change default wallet balance from 0.00 to 10000.00 INR

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_default_balance'
down_revision = '003_single_currency'
branch_labels = None
depends_on = None


def upgrade():
    # Update the default balance for wallets table
    op.alter_column('wallets', 'balance',
                    existing_type=sa.Numeric(precision=10, scale=2),
                    server_default='10000.00',
                    nullable=False)
    
    # Also update existing wallets that have 0 balance to 10000
    op.execute("UPDATE wallets SET balance = 10000.00 WHERE balance = 0.00")


def downgrade():
    # Revert back to 0.00 default
    op.alter_column('wallets', 'balance',
                    existing_type=sa.Numeric(precision=10, scale=2),
                    server_default='0.00',
                    nullable=False)
