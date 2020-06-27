"""empty message

Revision ID: c78a94961150
Revises: d3be0e0e351b
Create Date: 2020-06-26 21:54:16.124923

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c78a94961150'
down_revision = 'd3be0e0e351b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('operation', sa.Column('mec_power_delta_e', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('operation', 'mec_power_delta_e')
    # ### end Alembic commands ###
