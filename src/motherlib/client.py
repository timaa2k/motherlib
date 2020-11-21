import json
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
import retrying

from .model import AuthInfo, Record


DEFAULT_TIMEOUT = (3.05, 27)


class ConnectionError(Exception):
    pass


class APIError(Exception):

    def __init__(self, statuscode: int, kind: str, message: str, err: Optional[str]=None) -> None:
        super().__init__()
        self.statuscode = statuscode
        self.kind = kind
        self.message = message
        self.err = err

    @classmethod
    def FromHTTPResponse(cls, response: requests.Response) -> 'APIError':
        error = response.json()
        err = error.get('err', '')
        return cls(
            kind=error['kind'],
            message=error['message'],
            statuscode=response.status_code,
            err=None if err == '' else err,
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
        def retryfunc(e: Exception) -> bool:
            condition = False
            if isinstance(e, requests.exceptions.HTTPError):
                condition = e.response.status_code != 401
            return condition or isinstance(e, requests.exceptions.ConnectionError)

        @retrying.retry(
            stop_max_attempt_number=self.retries,
            retry_on_exception=retryfunc,
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

    def __init__(
        self,
        addr: str,
        bearer_token: Optional[str] = None,
        retries: int = 3,
    ) -> None:
        """
        List API client retry behavior.

        """
        self.addr = addr
        self.bearer_token = bearer_token
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
        if self.bearer_token is not None:
            headers['Authorization'] = 'Bearer ' + self.bearer_token
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

    def get_login_info(self, provider: str) -> 'AuthInfo':
        """
        Initiate the OAuth2 authentication flow for the specific Provider.

        The output presents a prepared URL which the user must visit in a browser
        to be asked to authenticate with an account of the specified provider.
        The account information is then used to determine the identity and the
        username of the user on the mothership side.

        Raises:
            APIError
        """
        response = self.request(
            method='GET',
            uri=f'/auth/{provider}/login',
            headers={'Accept': 'application/json'},
        )
        response.raise_for_status()
        return AuthInfo.unmarshal_json(response.json())

    def get_blob(self, ref: str) -> BytesIO:
        """
        Get the content for the specified digest ref.

        Raises:
            APIError
        """
        response = self.request(
            method='GET',
            uri=f'/blob/{ref}',
            headers={'Accept': 'application/octet-stream'},
        )
        response.raise_for_status()
        return BytesIO(response.content)

    def put_latest(self, tags: List[str], content: BytesIO) -> str:
        """
        Put the latest tagged content on the server.

        Raises:
            APIError
        """
        if len(tags) == 0:
            raise ValueError
        URI = '/'.join(tags)
        response = self.request(
            method='PUT',
            uri=f'/latest/{URI}',
            data=content,
        )
        response.raise_for_status()
        return response.headers['Location'].split('/blob/')[-1]

    def get_latest(self, tags: List[str]) -> List[Record]:
        """
        Return the matching records ordered backwards in time.

        Raises:
            APIError
        """
        URI='/'.join(tags)
        response = self.request(
            method='GET',
            uri=f'/latest/{URI}',
            headers={'Accept': 'application/json'},
        )
        response.raise_for_status()
        return [Record.unmarshal_json(i) for i in response.json()]

    def get_history(self, tags: List[str]) -> List[Record]:
        """
        Get the historical content from the server. Return the matching
        records ordered backwards in time.
        Raises:
            APIError
        """
        URI='/'.join(tags)
        response = self.request(
            method='GET',
            uri=f'/history/{URI}',
            headers={'Accept': 'application/json'},
        )
        response.raise_for_status()
        return [Record.unmarshal_json(i) for i in response.json()]

    def delete_history(self, tags: List[str]) -> None:
        """
        Delete content and all its history from the server.

        Raises:
            APIError
        """
        URI='/'.join(tags)
        response = self.request(
            method='DELETE',
            uri=f'/history/{URI}',
        )
        response.raise_for_status()
