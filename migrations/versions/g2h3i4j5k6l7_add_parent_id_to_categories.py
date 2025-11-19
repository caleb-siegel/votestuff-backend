"""Add parent_id to categories for subcategories

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2025-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'g2h3i4j5k6l7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # Add parent_id column to categories table
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.create_foreign_key('fk_categories_parent_id', 'categories', ['parent_id'], ['id'])
        batch_op.create_index('ix_categories_parent_id', ['parent_id'], unique=False)
    
    # Set all existing categories to have parent_id = NULL (top-level categories)
    op.execute("UPDATE categories SET parent_id = NULL")


def downgrade():
    # Remove parent_id column from categories table
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_index('ix_categories_parent_id')
        batch_op.drop_constraint('fk_categories_parent_id', type_='foreignkey')
        batch_op.drop_column('parent_id')



