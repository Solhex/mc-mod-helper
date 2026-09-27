"""Tests for the ModrinthAPI client."""

from unittest.mock import patch

from apis.modrinth_api import ModrinthAPI, MODRINTH_API_URL


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

    def test_updates_error_response_passthrough(self):
        api = ModrinthAPI()
        error = {'error': 'Timeout error occurred'}
        with patch.object(api, '_make_post_request', return_value=error):
            result = api.get_mod_updates_by_hash(
                ['hash1'], game_version='1.21', loader='fabric')
        assert result == error

    def test_get_mods_by_hash_returns_api_result_unchanged(self):
        api = ModrinthAPI()
        payload = {'abc': {'project_id': 'sodium', 'version_number': '2.0'}}
        with patch.object(api, '_make_post_request', return_value=payload):
            assert api.get_mods_by_hash(['abc']) == payload

    def test_custom_base_url(self):
        api = ModrinthAPI('https://mirror.example.org/v2')
        assert api.base_url == 'https://mirror.example.org/v2/'

    def test_existing_trailing_slash_not_doubled(self):
        api = ModrinthAPI(MODRINTH_API_URL + '/')
        assert api.base_url == MODRINTH_API_URL + '/'

    def test_uses_version_files_endpoint(self):
        api = ModrinthAPI()
        with patch.object(api, '_make_post_request',
                          return_value={}) as mock_request:
            api.get_mods_by_hash(['h'])
        assert mock_request.call_args[0][0] == 'version_files'

    def test_custom_hash_type_reaches_request_bodies(self):
        api = ModrinthAPI(hash_type='sha512')
        assert api.hash_type == 'sha512'
        with patch.object(api, '_make_post_request',
                          return_value={}) as mock_request:
            api.get_mods_by_hash(['h'])
        assert mock_request.call_args[0][1]['algorithm'] == 'sha512'
        with patch.object(api, '_make_post_request',
                          return_value={}) as mock_request:
            api.get_mod_updates_by_hash(
                ['h'], game_version='1.21', loader='fabric')
        assert mock_request.call_args[0][1]['algorithm'] == 'sha512'

    def test_get_mod_updates_wraps_every_hash(self):
        api = ModrinthAPI()
        with patch.object(api, '_make_post_request',
                          return_value={}) as mock_request:
            api.get_mod_updates_by_hash(
                ['hash1', 'hash2'], game_version='1.20.1', loader='forge')
        endpoint, body = mock_request.call_args[0]
        assert endpoint == 'version_files/update'
        assert body['hashes'] == ['hash1', 'hash2']
        assert body['loaders'] == ['forge']
        assert body['game_versions'] == ['1.20.1']
