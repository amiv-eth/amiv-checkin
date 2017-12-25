"""empty message

Revision ID: 48a2ceb37d6c
Revises: 
Create Date: 2017-12-25 16:51:00.128358

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '48a2ceb37d6c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('gvtool_events',
    sa.Column('_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=128), nullable=False),
    sa.Column('description', sa.String(length=10000), nullable=True),
    sa.Column('time_start', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('_id')
    )
    op.create_table('presencelists',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conn_type', sa.String(length=128), nullable=True),
    sa.Column('pin', sa.Integer(), nullable=True),
    sa.Column('token', sa.String(length=128), nullable=True),
    sa.Column('event_id', sa.String(length=128), nullable=True),
    sa.Column('event_ended', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_presencelists_pin'), 'presencelists', ['pin'], unique=True)
    op.create_table('gvtool_signups',
    sa.Column('_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(length=128), nullable=False),
    sa.Column('checked_in', sa.Boolean(), nullable=True),
    sa.Column('gvevent_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['gvevent_id'], ['gvtool_events._id'], ),
    sa.PrimaryKeyConstraint('_id'),
    sa.UniqueConstraint('user_id', 'gvevent_id')
    )
    op.create_table('gvtool_logs',
    sa.Column('_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('checked_in', sa.Boolean(), nullable=True),
    sa.Column('gvsignup_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['gvsignup_id'], ['gvtool_signups._id'], ),
    sa.PrimaryKeyConstraint('_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('gvtool_logs')
    op.drop_table('gvtool_signups')
    op.drop_index(op.f('ix_presencelists_pin'), table_name='presencelists')
    op.drop_table('presencelists')
    op.drop_table('gvtool_events')
    # ### end Alembic commands ###
