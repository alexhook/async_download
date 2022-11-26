import asyncio
import json
from asyncio import Queue
from typing import List, Optional, Dict, Union, Any

from .logging import LogMessage, logger
from .requests import BaseRequest
from .workers import BaseWorker


class ConcurrentRequests:
    def __init__(
            self,
            requests: List[BaseRequest],
            worker: BaseWorker,
            workers_count: int = 5,
    ):
        self.requests = requests
        self.worker = worker
        self.workers_count = workers_count

        self._workers = []
        self._queue = Queue()

    async def run(self) -> None:
        self.worker.queue = self._queue
        self._workers = [asyncio.create_task(self.worker.run()) for _ in range(self.workers_count)]
        for request in self.requests:
            self._queue.put_nowait(request)
        logger.info(LogMessage.start.value)
        await self._queue.join()

        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        logger.info(LogMessage.end.value)

    def get_content(self, raise_for_status: bool = False) -> List[Optional[bytes]]:
        content = []
        for request in self.requests:
            if raise_for_status:
                request.raise_for_status()
            content.append(request.response_content)
        return content

    def get_text_content(self, encoding: str = 'utf-8', raise_for_status: bool = False) -> List[Optional[str]]:
        text_content = []
        for content in self.get_content(raise_for_status=raise_for_status):
            if content:
                content = content.decode(encoding=encoding)
            text_content.append(content)
        return text_content

    def get_json_content(self, raise_for_status: bool = False) -> List[Optional[Union[List[Any], Dict[Any, Any]]]]:
        json_content = []
        for content in self.get_content(raise_for_status=raise_for_status):
            if content:
                content = json.loads(content)
            json_content.append(content)
        return json_content
