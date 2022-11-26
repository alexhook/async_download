from enum import Enum
import logging

logger = logging.getLogger('ConcurrentRequests')


class LogMessage(str, Enum):
    start = 'Starting to request...'
    end = 'All requests were completed.'
    success = 'Successful {method} request: {url} with data={data}, params={params}, headers={headers}'
    retry = 'Retry {method} request: {url} with data={data}, params={params}, headers={headers}'
    bad = 'Bad {method} request: {url} with data={data}, params={params}, headers={headers}'
