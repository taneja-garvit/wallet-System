"""fix_default_balance

Revision ID: 005_fix_default_balance
Revises: 004_default_balance
Create Date: 2026-10-14

Fix default wallet balance typo from 10000000000.00 (10 billion) to 10000.00 INR

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_fix_default_balance'
down_revision = '004_default_balance'
branch_labels = None
depends_on = None


def upgrade():
    # Set the correct server default for wallets balance column (10000.00 INR)
    op.alter_column('wallets', 'balance',
                    existing_type=sa.Numeric(precision=10, scale=2),
                    server_default='10000.00',
                    nullable=False)


def downgrade():
    # Revert back to previous server default
    op.alter_column('wallets', 'balance',
                    existing_type=sa.Numeric(precision=10, scale=2),
                    server_default='10000000000.00',
                    nullable=False)
