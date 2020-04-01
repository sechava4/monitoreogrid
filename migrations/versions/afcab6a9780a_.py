"""empty message

Revision ID: afcab6a9780a
Revises: 0738ca9ca091
Create Date: 2020-03-30 08:50:07.120029

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'afcab6a9780a'
down_revision = '0738ca9ca091'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('vehicle',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('placa', sa.String(length=64), nullable=True),
    sa.Column('marca', sa.String(length=64), nullable=True),
    sa.Column('modelo', sa.String(length=64), nullable=True),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('capacity_nominal', sa.Float(), nullable=True),
    sa.Column('soh', sa.Float(), nullable=True),
    sa.Column('rul', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_placa'), 'vehicle', ['placa'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_vehicle_placa'), table_name='vehicle')
    op.drop_table('vehicle')
    # ### end Alembic commands ###