"""Tests for BaseModApiClient construction and validation."""

import pytest

from apis.base import BaseModApiClient
from conftest import make_client


class TestBaseModApiClientInit:
    def test_appends_trailing_slash(self):
        client = make_client('https://api.example.com/v2')
        assert client.base_url == 'https://api.example.com/v2/'

    def test_keeps_existing_trailing_slash(self):
        client = make_client('https://api.example.com/v2/')
        assert client.base_url == 'https://api.example.com/v2/'

    @pytest.mark.parametrize('bad_url', [
        'not-a-url',
        'ftp://example.com',
        'example.com',
        'https://nodot',
    ])
    def test_rejects_invalid_url(self, bad_url):
        with pytest.raises(ValueError):
            BaseModApiClient(bad_url)

    def test_uses_default_headers_when_none_given(self):
        from apis import HEADERS
        client = make_client()
        assert client.headers == HEADERS

    def test_uses_custom_headers(self):
        headers = {'User-agent': 'test-agent'}
        client = BaseModApiClient('https://api.example.com', headers=headers)
        assert client.headers == headers
