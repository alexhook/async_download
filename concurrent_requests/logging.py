import logging
from enum import Enum

logger = logging.getLogger('ConcurrentRequests')


class LogMessage(str, Enum):
    start = 'Starting to request...'
    end = 'All requests were completed.'
    success = 'Successful {method} request: {url} with data={data}, params={params}, headers={headers}'
    retry = 'Retry {method} request: {url} with data={data}, params={params}, headers={headers}'
    bad = 'Bad {method} request: {url} with data={data}, params={params}, headers={headers}'


class ExceptionMessage(str, Enum):
    assert_base_file_request = 'The FileWorker expects to receive an instance of a BaseFileRequest class.'
