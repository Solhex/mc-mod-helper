__version__ = '1.1.1'

import logging
from . import BaseModApiClient

logger = logging.getLogger('root')

MODRINTH_API_URL = 'https://api.modrinth.com/v2'
logger.debug(f'Modrinth API URL: {MODRINTH_API_URL}')

class ModrinthAPI(BaseModApiClient):
    """Client for retrieving mod information from the Modrinth API."""

    def __init__(
            self,
            base_url: str = MODRINTH_API_URL,
            headers: dict | None = None,
            hash_type: str = 'sha1'):
        """Initialize the Modrinth API client

        If no base URL is provided, the modrinth API v2 URL is used.
        If no headers are provided, the default project headers are used.

        :param base_url: Optional alternative URL of the Modrinth API.
        :type base_url: str
        :param headers: Optional request headers.
        :type headers: dict | None
        :param hash_type: Hash type used for mod identification, defaults to 'sha1'.
        :type hash_type: str
        """

        super().__init__(base_url, headers)
        logger.info('Starting ModrinthAPI')
        logger.info(f'Modrinth API URL: {self.base_url}')
        self.hash_type = hash_type
        logger.debug(f'Modrinth Default Hash Type: {self.hash_type}')

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
            'version_files',
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
            'version_files/update',
            body)
