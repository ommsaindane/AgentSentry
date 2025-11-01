"""
add_rule_type_to_rules

Revision ID: 9b1a0b2c3d45
Revises: e0e559cddf50
Create Date: 2025-11-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9b1a0b2c3d45'
down_revision = 'e0e559cddf50'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('rules') as batch_op:
        batch_op.add_column(sa.Column('rule_type', sa.String(length=16), nullable=True))
    # Set default to 'regex' for existing rows
    op.execute("UPDATE rules SET rule_type = 'regex' WHERE rule_type IS NULL")
    # Make non-nullable going forward
    with op.batch_alter_table('rules') as batch_op:
        batch_op.alter_column('rule_type', existing_type=sa.String(length=16), nullable=False, server_default='regex')


def downgrade() -> None:
    with op.batch_alter_table('rules') as batch_op:
        batch_op.drop_column('rule_type')
