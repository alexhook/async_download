import asyncio
from typing import Any, List, Optional, Type

from aiohttp import ClientSession

from concurrent_requests.logging import LogMessage, logger
from concurrent_requests.requests import BaseRequest
from concurrent_requests.workers import BaseWorker, MemoryWorker


class ConcurrentRequests:
    __slots__ = (
        'session',
        'requests',
        'worker',
        'workers_count',
        'max_attempts',
        'delay',
        'worker_kwargs',
        '_workers',
        '_queue',
    )

    def __init__(
            self,
            session: ClientSession,
            requests: List[BaseRequest],
            *,
            worker: Type[BaseWorker] = MemoryWorker,
            workers_count: int = 5,
            max_attempts: int = 5,
            delay: float = 0,
            **worker_kwargs: Any,
    ):
        self.session = session
        self.requests = requests
        self.worker = worker
        self.workers_count = workers_count
        self.max_attempts = max_attempts
        self.delay = delay
        self.worker_kwargs = worker_kwargs

        self._workers = []
        self._queue = asyncio.Queue()

    async def run(self) -> None:
        self.worker = self.worker(
            session=self.session,
            queue=self._queue,
            max_attempts=self.max_attempts,
            delay=self.delay,
            **self.worker_kwargs,
        )

        self._workers = [
            asyncio.create_task(self.worker.run())
            for _ in range(self.workers_count)
        ]

        for request in self.requests:
            self._queue.put_nowait(request)
        logger.info(LogMessage.start.value)
        await self._queue.join()

        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        logger.info(LogMessage.end.value)

    def collect(self, raise_for_status: bool = False) -> List[Optional[bytes]]:
        if raise_for_status:
            self.raise_for_status()
        return [request.response_content for request in self.requests]

    def raise_for_status(self) -> None:
        for request in self.requests:
            request.raise_for_status()
