"""Add user_name

Revision ID: 80c93f8ae709
Revises: a6c45f27a93b
Create Date: 2021-06-04 00:02:03.298799

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '80c93f8ae709'
down_revision = 'a6c45f27a93b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('operation', sa.Column('user_name', sa.String(length=64), nullable=True))
    op.drop_column('operation', 'user_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('operation', sa.Column('user_id', mysql.VARCHAR(charset='utf8', collation='utf8_bin', length=64), nullable=True))
    op.drop_column('operation', 'user_name')
    # ### end Alembic commands ###
