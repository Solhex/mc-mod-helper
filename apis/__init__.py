__version__ = '1.3.0'
__all__ = ['base', 'modrinth_api']

import logging

logger = logging.getLogger('root')

USER_AGENT = f'Solhex/mc-mod-helper/{__version__} (contact@solfvern.com)'
logger.debug(f'User agent: {USER_AGENT}')
HEADERS = {'User-agent': USER_AGENT}
logger.debug(f'Headers: {HEADERS}')

from .base import BaseModApiClient
from . import modrinth_api
