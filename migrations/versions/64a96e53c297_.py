"""empty message

Revision ID: 64a96e53c297
Revises: 912be1c5ef93
Create Date: 2022-03-08 23:28:30.395040

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '64a96e53c297'
down_revision = '912be1c5ef93'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('artist', 'created_ts',
               existing_type=sa.VARCHAR(length=120),
               nullable=False,
               existing_server_default=sa.text('now()'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('artist', 'created_ts',
               existing_type=sa.VARCHAR(length=120),
               nullable=True,
               existing_server_default=sa.text('now()'))
    # ### end Alembic commands ###
