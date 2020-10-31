import json
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple, Union, Set

import requests
import retrying

from .model import Record, Result


DEFAULT_TIMEOUT = (3.05, 27)


class ConnectionError(Exception):
    pass


class APIError(Exception):

    def __init__(self, err: str, kind: str, statuscode: int) -> None:
        super().__init__()
        self.err = err
        self.kind = kind
        self.statuscode = statuscode

    @classmethod
    def FromHTTPResponse(cls, response: requests.Response) -> 'APIError':
        error = response.json()
        return cls(
            err=error['err'],
            kind=error['kind'],
            statuscode=error['statuscode'],
        )


class HTTPClient:

    def __init__(
        self,
        verify: bool,
        timeout: Tuple[float, float] = DEFAULT_TIMEOUT,
        retries: int = 0,
    ) -> None:
        self.verify = verify
        self.timeout = timeout
        self.retries = retries

    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
    ) -> Union[requests.Response, Any]:
        """
        Retry HTTP request on ``ConnectionError`` and ``HTTPError``s.
        """
        @retrying.retry(
            stop_max_attempt_number=self.retries,
            retry_on_exception=lambda e: isinstance(
                e, requests.exceptions.ConnectionError) or isinstance(
                    e, requests.exceptions.HTTPError),
        )
        def do_request() -> requests.Response:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                data=data,
                verify=self.verify,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response
        return do_request()


class APIClient:

    def __init__(self, addr: str, retries: int = 3) -> None:
        """
        Set API client retry behavior.

        """
        self.addr = addr
        self.http = HTTPClient(verify=False, retries=retries)

    def request(
        self,
        method: str,
        uri: str,
        params: Dict[str, str] = {},
        headers: Dict[str, str] = {},
        data: Optional[str] = None,
    ) -> requests.Response:
        """
        Retry on any HTTP error.

        """
        try:
            return self.http.request(
                method=method,
                url=self.addr + uri,
                params=params,
                headers=headers,
                data=data,
            )
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError from exc
        except requests.exceptions.HTTPError as exc:
            raise APIError.FromHTTPResponse(exc.response)

    def put_latest(self, tags: Set[str], content: BytesIO) -> str:
        """
        Put the latest tagged content on the server.

        Raises:
            APIError
        """
        if len(tags) == 0:
            raise ValueError
        URI = '/'.join(list(tags))
        response = self.request(
            method='PUT',
            uri=f'/latest/{URI}',
            data=content,
        )
        response.raise_for_status()
        location = response.headers['Location']
        ref = location.split('/blob/')[-1]
        return ref

    def get_latest(self, tags: Set[str]) -> Result:
        """
        Get the latest tagged content from the server. If the content is
        uniquely identified return the content.  If the content is not uniquely
        identified return the matching records ordered backwards in time.

        Raises:
            APIError
        """
        if len(tags) == 0:
            raise ValueError
        URI = '/'.join(list(tags))
        response = self.request(
            method='GET',
            uri=f'/latest/{URI}',
            headers={'Accept': 'application/json'},
        )
        response.raise_for_status()

        try:
            blob = response.json()
        except json.decoder.JSONDecodeError:
            return Result(content=response.content)

        records = []
        for item in blob:
            r = Record.unmarshal_json(item)
            records.append(r)
        return records

    def get_history(self, tags: Set[str]) -> List[Record]:
        """
        Get the historical tagged content from the server. Return the matching
        records ordered backwards in time.
        Raises:
            APIError
        """
        if len(tags) == 0:
            raise ValueError
        URI = '/'.join(list(tags))
        response = self.request(
            method='GET',
            uri=f'/history/{URI}',
            headers={'Accept': 'application/json'},
        )
        payload = response.json()
        import pdb; pdb.set_trace()
        records = []
        r = Record.unmarshal_json(payload)
        records.append(r)
        return records

    def delete_history(self, tags: Set[str]) -> None:
        """
        Delete tagged content and all its history.

        Raises:
            APIError
        """
        if len(tags) == 0:
            raise ValueError
        URI = '/'.join(list(tags))
        response = self.request(
            method='DELETE',
            uri=f'/history/{URI}',
        )
