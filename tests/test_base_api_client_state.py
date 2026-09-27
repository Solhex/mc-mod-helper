"""Tests for state held by BaseModApiClient instances."""

import requests

from conftest import make_client


class TestBaseModApiClientState:
    def test_each_client_gets_its_own_session(self):
        first = make_client()
        second = make_client()
        assert isinstance(first._session, requests.Session)
        assert first._session is not second._session

    def test_default_headers_are_the_shared_project_headers(self):
        from apis import HEADERS
        assert make_client().headers is HEADERS
