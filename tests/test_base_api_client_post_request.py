"""Tests for BaseModApiClient._make_post_request."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout

from apis.base import DEFAULT_TIMEOUT
from conftest import make_client


class TestMakePostRequest:
    def _mock_response(self, json_data=None):
        response = MagicMock()
        response.json.return_value = json_data if json_data is not None else {}
        response.status_code = 200
        return response

    def test_builds_url_without_double_slash(self):
        client = make_client()
        response = self._mock_response({'ok': True})
        with patch.object(client._session, 'post',
                          return_value=response) as mock_post:
            result = client._make_post_request('version_files', {'a': 1})
        called_url = mock_post.call_args[0][0]
        assert called_url == 'https://api.example.com/v2/version_files'
        assert '//version_files' not in called_url
        assert result == {'ok': True}

    def test_strips_leading_slash_from_method(self):
        client = make_client()
        response = self._mock_response()
        with patch.object(client._session, 'post',
                          return_value=response) as mock_post:
            client._make_post_request('/version_files', {})
        assert mock_post.call_args[0][0] == \
            'https://api.example.com/v2/version_files'

    def test_sets_default_timeout(self):
        client = make_client()
        response = self._mock_response()
        with patch.object(client._session, 'post',
                          return_value=response) as mock_post:
            client._make_post_request('version_files', {})
        assert mock_post.call_args[1]['timeout'] == DEFAULT_TIMEOUT

    def test_custom_timeout_not_overridden(self):
        client = make_client()
        response = self._mock_response()
        with patch.object(client._session, 'post',
                          return_value=response) as mock_post:
            client._make_post_request('version_files', {}, timeout=5)
        assert mock_post.call_args[1]['timeout'] == 5

    def test_sends_body_as_json_with_headers(self):
        client = make_client()
        response = self._mock_response()
        body = {'hashes': ['abc'], 'algorithm': 'sha1'}
        with patch.object(client._session, 'post',
                          return_value=response) as mock_post:
            client._make_post_request('version_files', body)
        assert mock_post.call_args[1]['json'] == body
        assert mock_post.call_args[1]['headers'] == client.headers

    @pytest.mark.parametrize('exception', [
        HTTPError('boom'),
        ConnectionError('boom'),
        Timeout('boom'),
        requests.RequestException('boom'),
    ])
    def test_returns_error_dict_on_request_failure(self, exception):
        client = make_client()
        with patch.object(client._session, 'post', side_effect=exception):
            result = client._make_post_request('version_files', {})
        assert 'error' in result

    def test_http_error_from_status_returns_error_dict(self):
        client = make_client()
        response = MagicMock()
        response.raise_for_status.side_effect = HTTPError('404')
        with patch.object(client._session, 'post', return_value=response):
            result = client._make_post_request('version_files', {})
        assert 'error' in result
