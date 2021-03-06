"""Add noi1_migration_info table

Revision ID: 1520c933a172
Revises: 1e1fc3825671
Create Date: 2016-01-21 00:27:58.273836

"""

# revision identifiers, used by Alembic.
revision = '1520c933a172'
down_revision = '1e1fc3825671'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('noi1_migration_info',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('noi1_userid', sa.String(), nullable=True),
    sa.Column('noi1_json', sa.Text(), nullable=True),
    sa.Column('email_sent_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('noi1_migration_info')
    ### end Alembic commands ###
