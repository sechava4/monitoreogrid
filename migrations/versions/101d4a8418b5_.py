"""empty message

Revision ID: 101d4a8418b5
Revises: ddc0219e2064
Create Date: 2020-07-09 23:35:57.151963

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "101d4a8418b5"
down_revision = "ddc0219e2064"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("operation", sa.Column("en_pot", sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("operation", "en_pot")
    # ### end Alembic commands ###
