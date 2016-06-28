"""empty message

Revision ID: 39d0fc7c8216
Revises: 902e1bf2855
Create Date: 2016-06-28 13:17:53.167954

"""

# revision identifiers, used by Alembic.
revision = '39d0fc7c8216'
down_revision = '902e1bf2855'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('users',
        sa.Column('repeat_tutorials', sa.Boolean, nullable=False, server_default=sa.DefaultClause('False'))
    )

def downgrade():
    pass
