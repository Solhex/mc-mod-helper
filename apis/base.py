import logging
import re
from abc import ABC

import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout

from . import HEADERS

logger = logging.getLogger('root')


class BaseModApiClient(ABC):
    """Base client for making requests to a mod-hosting API.

    Provides shared request behavior for API-specific clients, including
    base URL validation, default headers, POST request handling, error
    logging, and JSON response parsing.

    :param base_url: Base URL of the mod-hosting API.
    :type base_url: str
    :param headers: Optional HTTP headers to send with requests. If not
        provided, the default project headers are used.
    :type headers: dict | None
    """

    def __init__(
            self,
            base_url: str,
            headers: dict | None = None):
        """Initialize the API client.

        Validates and stores the base URL, ensuring it ends with a trailing
        slash. If no headers are provided, the default project headers are used.

        :param base_url: Base URL of the API.
        :type base_url: str
        :param headers: Optional request headers.
        :type headers: dict | None
        :raises Exception: If base_url is not a valid HTTP or HTTPS URL.
        """

        url_pattern = r'^(https?://)[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}'
        if not re.match(url_pattern, base_url):
            raise Exception(f'Invalid URL: {base_url}')

        self.base_url = base_url if base_url[-1] == '/' else base_url + '/'
        self.headers = headers if headers is not None else HEADERS

    def _make_post_request(
            self,
            method: str,
            body: dict,
            **kwargs: dict) -> dict:
        """Send a POST request to an API endpoint.

        Builds the request URL from the stored base URL and the provided
        endpoint path, sends the request body as JSON, logs request details,
        and returns the parsed JSON response.

        If the request fails, an error dictionary is returned instead.

        :param method: Endpoint path relative to the base URL.
        :type method: str
        :param body: JSON-serializable request body.
        :type body: dict
        :return: Parsed JSON response, or an error dictionary if the request fails.
        :rtype: dict
        """

        if method[0] == '/':
            method = method[1:]
        try:
            response = requests.post(
                '/'.join((self.base_url, method)),
                json=body,
                headers=self.headers,
                **kwargs)
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
