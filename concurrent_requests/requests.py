from typing import Optional


class BaseRequest:
    __method__: str

    def __init__(
            self,
            url: str,
            params: Optional[dict] = None,
            headers: Optional[dict] = None,
            data: Optional[dict] = None,
    ):
        self.url = url
        self.params = params
        self.headers = headers
        self.data = data

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
        return bool(self.exception)

    def raise_for_status(self) -> None:
        if self.has_exception:
            raise self.exception


class GET(BaseRequest):
    __method__ = 'get'


class POST(BaseRequest):
    __method__ = 'post'


class PUT(BaseRequest):
    __method__ = 'put'


class PATCH(BaseRequest):
    __method__ = 'patch'


class DELETE(BaseRequest):
    __method__ = 'delete'
