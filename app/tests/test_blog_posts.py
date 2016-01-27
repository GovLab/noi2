import unittest

from .. import blog_posts

class Blob(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def create_fake_feed(entries):
    return Blob(entries=entries)

class BlogPostsTests(unittest.TestCase):
    def test_summarize_works(self):
        self.assertEqual(
            blog_posts.summarize(create_fake_feed([
                Blob(description='a b', title='title', link='http://foo'),
                Blob(title='this one should never be examined')
            ]), max_entries=1, max_words_per_entry=1),
            [{
                'title': 'title',
                'description': u'a\u2026',
                'link': 'http://foo',
                'domain': 'foo'
            }]
        )
