"""Add RFIDLog table

Revision ID: fcca4e5e2050
Revises: 1a2d679ec467
Create Date: 2025-07-19 22:13:44.277176

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fcca4e5e2050'
down_revision = '1a2d679ec467'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('rfid_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('zone_name', sa.String(length=100), nullable=False),
    sa.Column('uid_submitted', sa.String(length=50), nullable=False),
    sa.Column('result', sa.String(length=50), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('rfid_log')
    # ### end Alembic commands ###
