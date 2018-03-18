"""empty message

Revision ID: 011f46b4f41d
Revises: d003c7685eab
Create Date: 2018-03-17 22:17:19.474509

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011f46b4f41d'
down_revision = 'd003c7685eab'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('presencelists', sa.Column('event_max_counter', sa.Integer(), nullable=True))
    op.add_column('presencelists', sa.Column('event_type', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('presencelists', 'event_type')
    op.drop_column('presencelists', 'event_max_counter')
    # ### end Alembic commands ###
