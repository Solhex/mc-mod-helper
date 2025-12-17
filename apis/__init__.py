__version__ = '1.1.0'
__all__ = ['modrinth_api']

import logging

logger = logging.getLogger('root')

MODRINTH_API_URL = 'https://api.modrinth.com/v2'
logger.debug(f'Modrinth API URL: {MODRINTH_API_URL}')
USER_AGENT = f'Solhex/easy-minecraft-mods-updater/{__version__} (contact@solfvern.com)'
logger.debug(f'User agent: {USER_AGENT}')
HEADERS = {'User-agent': USER_AGENT}
logger.debug(f'Headers: {HEADERS}')

from . import modrinth_api
