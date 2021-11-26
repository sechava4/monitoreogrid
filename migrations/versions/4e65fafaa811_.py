"""empty message

Revision ID: 4e65fafaa811
Revises: b9bc56b9706f
Create Date: 2020-05-22 11:34:24.477494

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4e65fafaa811"
down_revision = "b9bc56b9706f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "station",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("elevation", sa.Float(), nullable=True),
        sa.Column("charger_types", sa.String(length=64), nullable=True),
        sa.Column("number_of_chargers", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_station_name"), "station", ["name"], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_station_name"), table_name="station")
    op.drop_table("station")
    # ### end Alembic commands ###
