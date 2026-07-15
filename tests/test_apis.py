"""Tests for the apis package (BaseModApiClient and ModrinthAPI)."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout

from apis.base import BaseModApiClient, DEFAULT_TIMEOUT
from apis.modrinth_api import ModrinthAPI, MODRINTH_API_URL


def make_client(base_url='https://api.example.com/v2'):
    return BaseModApiClient(base_url)


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


class TestModrinthAPI:
    def test_default_base_url(self):
        api = ModrinthAPI()
        assert api.base_url == MODRINTH_API_URL + '/'

    def test_default_hash_type(self):
        api = ModrinthAPI()
        assert api.hash_type == 'sha1'

    def test_get_mods_by_hash_body(self):
        api = ModrinthAPI()
        with patch.object(api, '_make_post_request',
                          return_value={}) as mock_request:
            api.get_mods_by_hash(['hash1', 'hash2'])
        mock_request.assert_called_once_with(
            'version_files',
            {'hashes': ['hash1', 'hash2'], 'algorithm': 'sha1'})

    def test_get_mod_updates_by_hash_body(self):
        api = ModrinthAPI()
        with patch.object(api, '_make_post_request',
                          return_value={}) as mock_request:
            api.get_mod_updates_by_hash(
                ['hash1'], game_version='1.21', loader='fabric')
        mock_request.assert_called_once_with(
            'version_files/update',
            {'hashes': ['hash1'],
             'algorithm': 'sha1',
             'loaders': ['fabric'],
             'game_versions': ['1.21']})

    def test_error_response_passthrough(self):
        api = ModrinthAPI()
        error = {'error': 'HTTP error occurred: 404'}
        with patch.object(api, '_make_post_request', return_value=error):
            assert api.get_mods_by_hash(['hash1']) == error
