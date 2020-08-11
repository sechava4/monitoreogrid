"""empty message

Revision ID: 34c03031997c
Revises: dd030ba1820a
Create Date: 2020-08-11 09:47:30.445669

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '34c03031997c'
down_revision = 'dd030ba1820a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('operation', sa.Column('charge_current', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('operation', 'charge_current')
    # ### end Alembic commands ###
