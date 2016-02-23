import requests

from .config import config

def request(method, url, username=None, **kwargs):
    if username is None:
        username = config.admin_username

    params = kwargs.get('params', {})
    params['api_key'] = config.api_key
    params['api_username'] = username
    kwargs['params'] = params

    return requests.request(method, config.url(url), **kwargs)

def get(url, **kwargs):
    return request('get', url, **kwargs)

def post(url, **kwargs):
    return request('post', url, **kwargs)
