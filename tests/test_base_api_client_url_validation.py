"""Tests for BaseModApiClient base URL validation."""

import pytest

from apis.base import BaseModApiClient


class TestBaseModApiClientUrlValidation:
    @pytest.mark.parametrize('url', [
        'https://example.com',
        'http://example.com',
        'https://sub.domain.example.com/some/path',
        'https://example.com:8080/v2',
    ])
    def test_accepts_http_and_https_urls(self, url):
        assert BaseModApiClient(url).base_url == url + '/'

    @pytest.mark.parametrize('bad_url', [
        'https://',
        'http://',
        'HTTPS://example.com',
        '//example.com',
        'http:/example.com',
    ])
    def test_rejects_malformed_urls(self, bad_url):
        with pytest.raises(ValueError):
            BaseModApiClient(bad_url)

    def test_rejects_non_string_url(self):
        with pytest.raises(TypeError):
            BaseModApiClient(None)  # type: ignore[arg-type]
