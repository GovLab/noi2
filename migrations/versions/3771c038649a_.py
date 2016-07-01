"""empty message

Revision ID: 3771c038649a
Revises: 88b8e54d54b
Create Date: 2016-07-01 21:12:15.429312

"""

# revision identifiers, used by Alembic.
revision = '3771c038649a'
down_revision = '343b0090cb3e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('users',
        'show_sticky'
    )
    op.drop_column('users',
        'repeat_tutorials'
    )
    op.add_column('users',
        sa.Column('repeat_tutorials', sa.Boolean, nullable=True, server_default='True')
    )
    op.add_column('users',
        sa.Column('show_sticky', sa.Boolean, nullable=True, server_default='True')
    )


def downgrade():
    pass
