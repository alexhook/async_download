import asyncio
import os
from abc import ABC, abstractmethod
from typing import Any, AnyStr, Optional

import aiofiles
from aiohttp import ClientSession

from concurrent_requests.logging import ExceptionMessage, LogMessage, logger
from concurrent_requests.requests import BaseFileRequest, BaseRequest


class BaseWorker(ABC):
    __slots__ = (
        'session',
        'queue',
        'max_attempts',
        'delay',
    )

    def __init__(
            self,
            session: ClientSession,
            queue: asyncio.Queue,
            max_attempts: int,
            delay: float,
            **kwargs: Any,
    ) -> None:
        self.session = session
        self.queue = queue
        self.max_attempts = max_attempts
        self.delay = delay

    async def run(self) -> None:
        while True:
            request: BaseRequest = await self.queue.get()
            request.attempts += 1
            try:
                response_content = await self._request(request=request)
            except Exception as exception:
                if request.attempts < self.max_attempts:
                    await self.queue.put(request)
                    logger.info(LogMessage.retry.format(
                        method=request.__method__,
                        url=request.url,
                        data=request.data,
                        params=request.params,
                        headers=request.headers,
                    ))
                else:
                    request._exception = exception
                    logger.info(LogMessage.bad.format(
                        method=request.__method__,
                        url=request.url,
                        data=request.data,
                        params=request.params,
                        headers=request.headers,
                    ))
            else:
                request._response_content = response_content
                logger.info(LogMessage.success.format(
                    method=request.__method__,
                    url=request.url,
                    data=request.data,
                    params=request.params,
                    headers=request.headers,
                ))
            self.queue.task_done()
            if self.delay:
                await asyncio.sleep(self.delay)

    @abstractmethod
    async def _request(self, request: BaseRequest) -> Optional[bytes]:
        pass


class MemoryWorker(BaseWorker):
    __slots__ = ()

    def __init__(
            self,
            session: ClientSession,
            queue: asyncio.Queue,
            max_attempts: int,
            delay: float,
    ) -> None:
        super().__init__(session, queue, max_attempts, delay)

    async def _request(self, request: BaseRequest) -> bytes:
        async with self.session.request(
                method=request.__method__,
                url=request.url,
                data=request.data,
                params=request.params,
                headers=request.headers,
                **request.kwargs,
        ) as response:
            return await response.read()


class FileWorker(BaseWorker):
    __slots__ = ('path', )

    def __init__(
            self,
            session: ClientSession,
            queue: asyncio.Queue,
            max_attempts: int,
            delay: float,
            path: AnyStr,
    ) -> None:
        super().__init__(session, queue, max_attempts, delay)
        self.path = path

    async def _request(self, request: BaseFileRequest) -> None:
        assert isinstance(request, BaseFileRequest), ExceptionMessage.assert_base_file_request.value
        file_path = os.path.join(self.path, request.file_name)
        async with aiofiles.open(file_path, mode='wb') as save_file:
            async with self.session.request(
                    method=request.__method__,
                    url=request.url,
                    data=request.data,
                    params=request.params,
                    headers=request.headers,
                    **request.kwargs,
            ) as response:
                async for chunk in response.content.iter_chunked(1024):
                    await save_file.write(chunk)
