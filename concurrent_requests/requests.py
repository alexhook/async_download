from abc import ABC
from typing import Any, Optional

from aiohttp.hdrs import METH_DELETE, METH_GET, METH_HEAD, METH_OPTIONS, METH_PATCH, METH_POST, METH_PUT
from aiohttp.typedefs import LooseHeaders, StrOrURL


class BaseRequest(ABC):
    __slots__ = (
        'url',
        'data',
        'params',
        'headers',
        'kwargs',
        'attempts',
        '_exception',
        '_response_content',
    )

    __method__: str

    def __init__(
            self,
            url: StrOrURL,
            data: Any = None,
            params: Optional[StrOrURL] = None,
            headers: Optional[LooseHeaders] = None,
            **kwargs: Any,
    ):
        self.url = url
        self.data = data
        self.params = params
        self.headers = headers
        self.kwargs = kwargs

        self.attempts: int = 0
        self._exception: Optional[Exception] = None
        self._response_content: Optional[bytes] = None

    @property
    def response_content(self) -> Optional[bytes]:
        return self._response_content

    @property
    def exception(self) -> Optional[Exception]:
        return self._exception

    @property
    def has_exception(self) -> bool:
        return bool(self._exception)

    def raise_for_status(self) -> None:
        if self.has_exception:
            raise self._exception


class BaseFileRequest(BaseRequest, ABC):
    __slots__ = ('file_name', )

    file_name: str


class GET(BaseRequest):
    __slots__ = ()

    __method__ = METH_GET

    def __init__(self, url: StrOrURL, **kwargs: Any):
        super().__init__(url, **kwargs)


class POST(BaseRequest):
    __slots__ = ()

    __method__ = METH_POST

    def __init__(self, url: StrOrURL, data: Any = None, **kwargs: Any):
        super().__init__(url, data=data, **kwargs)


class PUT(BaseRequest):
    __slots__ = ()

    __method__ = METH_PUT

    def __init__(self, url: StrOrURL, data: Any = None, **kwargs: Any):
        super().__init__(url, data=data, **kwargs)


class PATCH(BaseRequest):
    __slots__ = ()

    __method__ = METH_PATCH

    def __init__(self, url: StrOrURL, data: Any = None, **kwargs: Any):
        super().__init__(url, data=data, **kwargs)


class DELETE(BaseRequest):
    __slots__ = ()

    __method__ = METH_DELETE

    def __init__(self, url: StrOrURL, **kwargs: Any):
        super().__init__(url, **kwargs)


class OPTIONS(BaseRequest):
    __slots__ = ()

    __method__ = METH_OPTIONS

    def __init__(self, url: StrOrURL, **kwargs: Any):
        super().__init__(url, **kwargs)


class HEAD(BaseRequest):
    __slots__ = ()

    __method__ = METH_HEAD

    def __init__(self, url: StrOrURL, **kwargs: Any):
        super().__init__(url, **kwargs)


class FileGET(BaseFileRequest, GET):
    __slots__ = ()

    def __init__(self, url: StrOrURL, file_name: str, **kwargs: Any):
        super().__init__(url, **kwargs)
        self.file_name = file_name


class FilePOST(BaseFileRequest, POST):
    __slots__ = ()

    def __init__(self, url: StrOrURL, file_name: str, data: Any = None, **kwargs: Any):
        super().__init__(url, data=data, **kwargs)
        self.file_name = file_name
