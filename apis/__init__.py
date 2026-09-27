# Single source of truth. Generated from git tags by
# scripts/update_version.py, so no version here is ever bumped by hand.
# Every other module re-exports this one value.
from ._version import __version__

__all__ = ['base', 'modrinth_api', 'BaseModApiClient']

import logging

logger = logging.getLogger(__name__)

USER_AGENT = f'Solhex/mc-mod-helper/{__version__} (contact@solfvern.com)'
logger.debug(f'User agent: {USER_AGENT}')
HEADERS = {'User-agent': USER_AGENT}
logger.debug(f'Headers: {HEADERS}')

from .base import BaseModApiClient
from . import modrinth_api
