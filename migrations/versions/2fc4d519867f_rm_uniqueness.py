"""rm uniqueness

Revision ID: 2fc4d519867f
Revises: 8d7d9e1b4f4f
Create Date: 2021-09-29 18:23:45.115177

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2fc4d519867f"
down_revision = "8d7d9e1b4f4f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_vehicle_placa", table_name="vehicle")
    op.create_index(op.f("ix_vehicle_placa"), "vehicle", ["placa"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_vehicle_placa"), table_name="vehicle")
    op.create_index("ix_vehicle_placa", "vehicle", ["placa"], unique=True)
    # ### end Alembic commands ###
