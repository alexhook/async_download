import asyncio
from abc import abstractmethod
from asyncio import Queue

from aiohttp import ClientSession

from .logging import LogMessage, logger
from .requests import BaseRequest


class BaseWorker:
    queue: Queue

    def __init__(self, session: ClientSession, max_attempts: int = 5, delay: float = 0) -> None:
        self.session = session
        self.max_attempts = max_attempts
        self.delay = delay

    @abstractmethod
    async def run(self) -> None:
        pass


class MemoryWorker(BaseWorker):
    async def make_request(self, request: BaseRequest):
        async with self.session.request(
                method=request.__method__,
                url=request.url,
                params=request.params,
                headers=request.headers,
        ) as response:
            return await response.read()

    async def run(self) -> None:
        while True:
            request: BaseRequest = await self.queue.get()
            try:
                response_content = await self.make_request(request=request)
            except Exception as exception:
                request.attempts += 1
                if request.attempts < self.max_attempts:
                    logger.info(LogMessage.retry.format(
                        method=request.__method__.upper(),
                        url=request.url,
                        data=request.data,
                        params=request.params,
                        headers=request.headers,
                    ))
                    await self.queue.put(request)
                else:
                    request._exception = exception
                    logger.info(LogMessage.bad.format(
                        method=request.__method__.upper(),
                        url=request.url,
                        data=request.data,
                        params=request.params,
                        headers=request.headers,
                    ))
            else:
                logger.info(LogMessage.success.format(
                    method=request.__method__.upper(),
                    url=request.url,
                    data=request.data,
                    params=request.params,
                    headers=request.headers,
                ))
                request._response_content = response_content
            self.queue.task_done()
            if self.delay:
                await asyncio.sleep(self.delay)
