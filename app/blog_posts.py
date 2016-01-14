import urlparse
import bleach
from flask import Markup

def truncate(text, max_words):
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
