import datetime
from sqlalchemy import types, Column, ForeignKey

from ..models import db
from .. import models
from . import api
from .config import config

# http://stackoverflow.com/a/127972/2422398
def parse_iso_datetime(text):
    return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ")

class DiscourseTopicEvent(models.Event):
    discourse_id = Column(types.Integer, unique=True)

    slug = Column(types.Text)

    excerpt = Column(types.Text)

    title = Column(types.Text)

    reply_count = Column(types.Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'discourse_topic_event'
    }

    @property
    def url(self):
        return config.url('/t/%s/%d' % (self.slug, self.discourse_id))

    @classmethod
    def _get_or_create(cls, discourse_id):
        msg = db.session.query(cls).\
              filter_by(discourse_id=discourse_id).first()
        if msg is None:
            msg = cls(discourse_id=discourse_id)
        return msg

    @classmethod
    def _update_category(cls, category):
        topics = category.get('topics', [])
        for topic in topics:
            if not topic['visible']: continue
            msg = cls._get_or_create(discourse_id=topic['id'])
            msg.created_at = parse_iso_datetime(topic['created_at'])
            msg.updated_at = parse_iso_datetime(topic['bumped_at'])
            msg.slug = topic['slug']

            # Argh, it looks like only pinned topics have excerpts
            # for now:
            #
            # https://meta.discourse.org/t/get-excerpt-for-regular-topics/33482
            msg.excerpt = topic.get('excerpt')

            msg.title = topic['title']
            msg.reply_count = topic['reply_count']
            db.session.add(msg)

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
        type_name = cls.__mapper_args__['polymorphic_identity']
        db.session.query(models.Event).\
          filter(models.Event.type==type_name).\
          delete()
        db.session.commit()
