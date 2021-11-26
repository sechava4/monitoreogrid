"""empty message

Revision ID: b278714fd81c
Revises: 9babf2a93d40
Create Date: 2020-12-09 10:07:48.929849

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b278714fd81c"
down_revision = "9babf2a93d40"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("operation", sa.Column("kwh_km", sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("operation", "kwh_km")
    # ### end Alembic commands ###
