__version__ = '1.0.1'

import logging
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
from . import MODRINTH_API_URL, HEADERS

logger = logging.getLogger('root')

class RequestFailedError(Exception):
    pass

class ModrinthApi:
    """This class is for getting mod information using the modrinth
    API.

    :param mod_api_url: URL of the Modrinth api,
        default value in __init__, defaults to MODRINTH_API_URL
    :type mod_api_url: str, optional
    :param api_headers: Headers to send with the Request,
        defaults to HEADERS
    :type api_headers: dict, optional
    :param hash_type: Hash type to be used,
        defaults to 'sha1'
    :type hash_type: str, optional
    """

    def __init__(
            self,
            mod_api_url=MODRINTH_API_URL,
            api_headers=HEADERS,
            default_hash_type='sha1'):
        """Constructor method"""
        logger.info('Starting ModrinthApi')
        self.api_url = mod_api_url
        self.headers = api_headers
        self.hash_type = default_hash_type
        logger.info(f'Modrinth API URL: {self.api_url}')

    def _make_post_request(
            self,
            request_url: str,
            request_body: dict) -> dict:
        try:
            response = requests.post(
                request_url,
                json=request_body,
                headers=self.headers)
            response.raise_for_status()
        except HTTPError as err:
            logger.error(f'HTTP error occurred: {err}')
            return {'error': f'HTTP error occurred: {err}'}
        except ConnectionError as err:
            logger.error(f'Connection error occurred: {err}')
            return {'error': 'Connection error occurred'}
        except Timeout as err:
            logger.error(f'Timeout error occurred: {err}')
            return {'error': 'Timeout error occurred'}
        except requests.RequestException as err:
            logger.error(f'Request exception occurred: {err}')
            return {'error': 'Failed to retrieve data. See log for more details.'}

        logger.info(f'Request: {response.request.method} {response.request.url} - '
                     f'Status: {response.status_code}')
        logger.debug(f'Request headers: {response.request.headers}')
        logger.debug(f'Request body: {response.request.body}')
        logger.debug(f'Request content: {response.text}')

        return response.json()

    def get_multiple_mods_details(
            self,
            mod_hash_list: list) -> dict:
        """Returns a dictionary of each mod in mod_hash_list.

        :param mod_hash_list: List of mod hashes
        :type mod_hash_list: list
        :return: Dictionary of each mod's details in mod_hash_list,
            may return empty dictionary if an error occurs
        :rtype: dict
        """
        logger.info(f'Starting get_multiple_mods_details')
        body = {
            'hashes': mod_hash_list,
            'algorithm': self.hash_type
        }

        return self._make_post_request(
            f'{self.api_url}/version_files',
            body)

    def get_multiple_mods_update_info(
            self,
            mod_hash_list: list,
            game_version: str,
            loader: str) -> dict:
        """Returns a dictionary of the latest version of each mod in
        mod_hash_list.

        :param mod_hash_list: List of mod hashes
        :type mod_hash_list: list
        :param game_version: Version of the game to get compatible
            mod versions
        :type game_version: list
        :param loader: Mod loader to get compatible mods
        :type loader: str
        :return: Dictionary of each mod's latest version details,
            may return empty dictionary if an error occurs
        :rtype: dict
        """
        logger.info(f'Starting get_multiple_mods_update_info')
        body = {
            'hashes': mod_hash_list,
            'algorithm': self.hash_type,
            'loaders': [loader],
            'game_versions': [game_version]
        }
        return self._make_post_request(
            f'{self.api_url}/version_files/update',
            body)
