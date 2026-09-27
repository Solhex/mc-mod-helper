"""Tests driving BaseModApiClient through the real requests stack."""

import json
import pytest

from conftest import RecordingAdapter, make_client


class TestBaseModApiClientRealTransport:
    """Tests exercising the real requests stack via a mounted adapter."""

    def _client_with_adapter(self, **kwargs):
        client = make_client()
        adapter = RecordingAdapter(**kwargs)
        client._session.mount('https://', adapter)
        return client, adapter

    def test_posts_json_body_to_assembled_url(self):
        client, adapter = self._client_with_adapter(
            body=b'{"version_number": "2.0"}')
        result = client._make_post_request('version_files',
                                           {'hashes': ['abc']})
        assert result == {'version_number': '2.0'}
        sent = adapter.requests[0]
        assert sent.method == 'POST'
        assert sent.url == 'https://api.example.com/v2/version_files'
        assert json.loads(sent.body) == {'hashes': ['abc']}
        assert sent.headers['Content-Type'] == 'application/json'
        assert sent.headers['User-agent'] == client.headers['User-agent']

    def test_leading_slash_method_hits_same_url(self):
        client, adapter = self._client_with_adapter()
        client._make_post_request('/version_files', {})
        assert adapter.requests[0].url == \
            'https://api.example.com/v2/version_files'

    @pytest.mark.parametrize('status_code', [400, 404, 500, 503])
    def test_error_status_returns_error_dict(self, status_code):
        client, adapter = self._client_with_adapter(
            status_code=status_code, body=b'{}')
        assert 'error' in client._make_post_request('version_files', {})
        assert len(adapter.requests) == 1

    def test_non_json_success_body_returns_error_dict(self):
        client, _ = self._client_with_adapter(
            status_code=200,
            body=b'<html>gateway error</html>',
            content_type='text/html')
        assert 'error' in client._make_post_request('version_files', {})

    def test_empty_body_returns_error_dict(self):
        client, _ = self._client_with_adapter(status_code=200, body=b'')
        assert 'error' in client._make_post_request('version_files', {})
