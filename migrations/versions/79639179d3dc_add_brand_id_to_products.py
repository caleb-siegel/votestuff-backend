"""add_brand_id_to_products

Revision ID: 79639179d3dc
Revises: g2h3i4j5k6l7
Create Date: 2025-11-30 07:38:46.852502

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '79639179d3dc'
down_revision = 'g2h3i4j5k6l7'
branch_labels = None
depends_on = None


def upgrade():
    # Add brand_id column to products table
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('brand_id', UUID(as_uuid=True), nullable=True))
        batch_op.create_foreign_key('fk_products_brand_id_retailers', 'retailers', ['brand_id'], ['id'])
        batch_op.create_index('ix_products_brand_id', ['brand_id'])


def downgrade():
    # Remove brand_id column from products table
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_index('ix_products_brand_id')
        batch_op.drop_constraint('fk_products_brand_id_retailers', type_='foreignkey')
        batch_op.drop_column('brand_id')
