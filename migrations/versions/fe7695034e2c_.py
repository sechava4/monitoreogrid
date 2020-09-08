"""empty message

Revision ID: fe7695034e2c
Revises: bda58e6c1818
Create Date: 2020-09-07 22:11:58.102165

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe7695034e2c'
down_revision = 'bda58e6c1818'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('vehicle', sa.Column('cd', sa.Integer(), nullable=True))
    op.add_column('vehicle', sa.Column('frontal_area', sa.Integer(), nullable=True))
    op.add_column('vehicle', sa.Column('weight', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('vehicle', 'weight')
    op.drop_column('vehicle', 'frontal_area')
    op.drop_column('vehicle', 'cd')
    # ### end Alembic commands ###
