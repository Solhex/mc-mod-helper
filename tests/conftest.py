"""Shared helpers for the apis test suite.

Kept in conftest.py so pytest puts tests/ on sys.path and every test module
can import these without packaging tests/ as a package.
"""

import requests
from requests.adapters import BaseAdapter

from apis.base import BaseModApiClient

DEFAULT_BASE_URL = 'https://api.example.com/v2'


def make_client(base_url=DEFAULT_BASE_URL):
    return BaseModApiClient(base_url)


class RecordingAdapter(BaseAdapter):
    """Transport adapter that records requests and replays a canned response.

    Mounting this on a session's adapter map exercises the real requests
    stack, so URL building, header injection and JSON encoding are all
    verified as they are actually sent over the wire.
    """

    def __init__(
            self,
            status_code=200,
            body=b'{}',
            content_type='application/json'):
        self.status_code = status_code
        self.body = body
        self.content_type = content_type
        self.requests = []

    def send(
            self,
            request,
            stream=False,
            timeout=None,
            verify=True,
            cert=None,
            proxies=None):
        self.requests.append(request)
        response = requests.Response()
        response.status_code = self.status_code
        response._content = self.body
        response.headers['Content-Type'] = self.content_type
        response.url = request.url or ''
        # _make_post_request logs response.request, which is normally set by
        # the real adapter.
        response.request = request
        return response

    def close(self):
        pass
