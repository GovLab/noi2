"""empty message

Revision ID: 343b0090cb3e
Revises: 39d0fc7c8216
Create Date: 2016-06-30 01:35:32.790698

"""

# revision identifiers, used by Alembic.
revision = '343b0090cb3e'
down_revision = '39d0fc7c8216'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('users',
        sa.Column('repeat_tutorials', sa.Boolean, nullable=False, server_default=sa.DefaultClause('True'))
    )
    op.add_column('users',
        sa.Column('show_sticky', sa.Boolean, nullable=False, server_default=sa.DefaultClause('True'))
    )


def downgrade():
    pass
