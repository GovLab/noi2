import urlparse
import bleach
from flask import Markup
import feedparser

def truncate(text, max_words):
    '''
    Truncates the given text with an ellipsis if it's more than the given
    number of words long.

    Examples:

        >>> truncate('bop', 1)
        'bop'

        >>> truncate('bop bap', 1)
        u'bop\u2026'
    '''

    words = text.split(' ')
    if len(words) <= max_words:
        return text
    return u' '.join(words[:max_words]) + u'\u2026'

def summarize(feed, max_entries=3, max_words_per_entry=20):
    posts = []
    for entry in feed.entries[:max_entries]:
        desc = truncate(entry.description, max_words_per_entry)
        post = dict(
            title=entry.title,
            description=Markup(bleach.clean(desc)),
            link=entry.link,
            domain=urlparse.urlparse(entry.link).netloc
        )
        posts.append(post)
    return posts

def get_and_summarize(url):
    d = feedparser.parse(url)
    return summarize(d)
