import asyncio
import json
from typing import List, Optional

from concurrent_requests.logging import LogMessage, logger
from concurrent_requests.requests import BaseRequest
from concurrent_requests.types import JSONType
from concurrent_requests.workers import BaseWorker


class ConcurrentRequests:
    __slots__ = (
        'requests',
        'worker',
        'workers_count',
        '_workers',
        '_queue',
    )

    def __init__(self, requests: List[BaseRequest], worker: BaseWorker, workers_count: int = 5):
        self.requests = requests
        self.worker = worker
        self.workers_count = workers_count

        self._workers = []
        self._queue = asyncio.Queue()

    async def run(self) -> None:
        self.worker.queue = self._queue
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
        responses_content = []
        for request in self.requests:
            if raise_for_status:
                request.raise_for_status()
            responses_content.append(request.response_content)
        return responses_content

    def collect_text(self, encoding: str = 'utf-8', raise_for_status: bool = False) -> List[Optional[str]]:
        responses_text_content = []
        for response_content in self.collect(raise_for_status=raise_for_status):
            if response_content:
                response_content = response_content.decode(encoding=encoding)
            responses_text_content.append(response_content)
        return responses_text_content

    def collect_json(self, raise_for_status: bool = False) -> List[Optional[JSONType]]:
        responses_json_content = []
        for response_content in self.collect(raise_for_status=raise_for_status):
            if response_content:
                response_content = json.loads(response_content)
            responses_json_content.append(response_content)
        return responses_json_content

    def raise_for_status(self) -> None:
        for request in self.requests:
            request.raise_for_status()
