import datetime
from sqlalchemy import types, Column, ForeignKey, UniqueConstraint

from ..models import db, User
from .. import models
from . import api
from .config import config

# http://stackoverflow.com/a/127972/2422398
def parse_iso_datetime(text):
    '''
    >>> parse_iso_datetime('2016-02-18T14:27:48.218Z')
    datetime.datetime(2016, 2, 18, 14, 27, 48, 218000)
    '''

    return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ")

class DiscourseTopicEvent(models.UserEvent):
    __tablename__ = 'discourse_topics'

    id = Column(types.Integer, ForeignKey('user_events.id'), primary_key=True)

    discourse_id = Column(types.Integer)

    post_number = Column(types.Integer)

    slug = Column(types.Text)

    excerpt = Column(types.Text)

    title = Column(types.Text)

    posts_count = Column(types.Integer)

    category_name = Column(types.Text)

    category_slug = Column(types.Text)

    __table_args__ = (UniqueConstraint('discourse_id', 'post_number'),)

    __mapper_args__ = {
        'polymorphic_identity': 'discourse_topic_event'
    }

    @property
    def url(self):
        return config.url('/t/%s/%d/%d' % (self.slug, self.discourse_id,
                                           self.post_number or 0))

    @property
    def category_url(self):
        return config.url('/c/%s' % self.category_slug)

    @classmethod
    def _get_or_create(cls, discourse_id, post_number=None):
        msg = db.session.query(cls).\
              filter_by(discourse_id=discourse_id,
                        post_number=post_number).first()
        if msg is None:
            msg = cls(discourse_id=discourse_id, post_number=post_number)
        return msg

    @classmethod
    def _update_topic(cls, category, topic):
        req = api.get('/t/%d/last.json' % topic['id'])

        if req.status_code != 200:
            return req.raise_for_status()

        topic_detail = req.json()

        for post in topic_detail['post_stream']['posts']:
            if post['hidden'] or not post['cooked']: continue

            msg = cls._get_or_create(discourse_id=topic['id'],
                                     post_number=post['post_number'])
            msg.created_at = parse_iso_datetime(post['created_at'])
            msg.updated_at = parse_iso_datetime(post['updated_at'])
            msg.slug = topic['slug']

            msg.category_name = category['name']
            msg.category_slug = category['slug']

            user = User.find_by_username(post['username'])
            msg.user = user

            msg.excerpt = post['cooked']

            msg.title = topic['title']
            msg.posts_count = topic['posts_count']
            db.session.add(msg)

    @classmethod
    def _update_category(cls, category):
        topics = category.get('topics', [])
        for topic in topics:
            if not topic['visible']: continue

            cls._update_topic(category, topic)

    @classmethod
    def update(cls):
        req = api.get('/categories.json')
        if req.status_code != 200:
            req.raise_for_status()
        categories = req.json()['category_list']['categories']

        for category in categories:
            if not category['read_restricted']:
                cls._update_category(category)

        db.session.commit()

    @classmethod
    def delete_all(cls):
        # Note that db.session.query(cls).delete() doesn't work because
        # it won't delete the "parent" rows from our superclass table(s).

        for obj in db.session.query(cls):
            db.session.delete(obj)

        db.session.commit()
