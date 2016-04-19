"""Add category_name, category_slug to discourse_topics

Revision ID: 312a48268855
Revises: 4309a04aaea9
Create Date: 2016-03-22 12:03:26.330530

"""

# revision identifiers, used by Alembic.
revision = '312a48268855'
down_revision = '4309a04aaea9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('discourse_topics', sa.Column('category_name', sa.Text(), nullable=True))
    op.add_column('discourse_topics', sa.Column('category_slug', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('discourse_topics', 'category_slug')
    op.drop_column('discourse_topics', 'category_name')
    ### end Alembic commands ###