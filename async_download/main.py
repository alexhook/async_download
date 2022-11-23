import asyncio
import itertools
import os
import random
from asyncio.exceptions import TimeoutError
from string import ascii_letters
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple, Union, Iterable

import aiofiles
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ServerDisconnectedError

CHUNK_SIZE = 1024
RANDOM_NAME_LEN = 6


async def worker(queue: asyncio.Queue, session: ClientSession, tmp_path: str, delay: Union[int, float]):
    while True:
        request_info = await queue.get()
        url, params, headers = request_info['url'], request_info['params'], request_info['headers']
        random_name = ''.join(random.choices(ascii_letters, k=RANDOM_NAME_LEN))

        try:
            async with session.get(url, params=params, headers=headers) as response:
                async with aiofiles.open(os.path.join(tmp_path, random_name), 'wb') as file:
                    async for data in response.content.iter_chunked(CHUNK_SIZE):
                        await file.write(data)
        except (TimeoutError, ServerDisconnectedError, ConnectionResetError):
            await queue.put(headers)

        if delay:
            await asyncio.sleep(delay)
        queue.task_done()


async def async_download(
        url: Union[Union[List[str], Tuple[str]], str],
        workers: int = 10,
        delay: Union[int, float] = 0,
        timeout: Optional[ClientTimeout] = ClientTimeout(total=5*60, connect=None, sock_connect=None, sock_read=None),
        request_params: Optional[Union[Iterable[dict], dict]] = None,
        request_headers: Optional[Union[Iterable[dict], dict]] = None,
) -> List[bytes]:
    results = []
    queue = asyncio.Queue()

    if not any(isinstance(obj, Union[List, Tuple]) for obj in (url, request_params, request_headers)):
        sequence = [(url, request_params, request_headers)]
    else:
        if isinstance(url, str):
            url = itertools.repeat(url)
        if isinstance(request_params, Optional[dict]):
            request_params = itertools.repeat(request_params)
        if isinstance(request_headers, Optional[dict]):
            request_headers = itertools.repeat(request_headers)
        sequence = zip(url, request_params, request_headers)

    for url, params, headers in sequence:
        queue.put_nowait({
            'url': url,
            'params': params,
            'headers': headers,
        })

    with TemporaryDirectory() as tmp_dir:
        async with ClientSession(raise_for_status=True, timeout=timeout) as session:
            tasks = [asyncio.create_task(worker(queue, session, tmp_dir, delay)) for _ in range(workers)]
            await queue.join()

        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        for filename in os.listdir(tmp_dir):
            with open(os.path.join(tmp_dir, filename), mode='rb') as file:
                results.append(file.read())

    return results
