import datetime
import uuid
from hashlib import sha256

import pytest
import responses
from http import HTTPStatus

from motherlib.client import APIClient


class TestAPIClient:

    @pytest.fixture()
    def api(self) -> 'APIClient':
        return APIClient(addr='http://api.mother.ship')

    @responses.activate
    def test_get_blob(self, api: APIClient) -> None:
        test_content = str.encode(str(uuid.uuid4()))
        test_ref = sha256(content).hexdigest()
        responses.add(
            method=responses.GET,
            url=f'{api.addr}/blob/{test_ref}',
            status=HTTPStatus.STATUS_OK.value,
            content_type='application/octet-stream',
            body=test_content,
        )
        content = api.get_blob(ref=test_ref)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/blob/{test_ref}'
        assert content == test_content

    @responses.activate
    def test_put_latest(self, api: APIClient) -> None:
        tags = set(['log', 'development'])
        content = str.encode(str(uuid.uuid4()))
        test_ref = sha256(content).hexdigest()
        URI = '/'.join(list(tags))
        responses.add(
            method=responses.PUT,
            url=f'{api.addr}/latest/{URI}',
            headers={'Location': f'{api.addr}/blob/{test_ref}'},
            status=HTTPStatus.NO_CONTENT.value,
        )
        ref = api.put_latest(tags=tags, content=content)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/latest/{URI}'
        assert ref == test_ref

    @responses.activate
    def test_get_latest_single(self, api: APIClient) -> None:
        tags = set(['log', 'development'])
        URI = '/'.join(list(tags))
        responses.add(
            method=responses.GET,
            url=f'{api.addr}/latest/{URI}',
            status=HTTPStatus.OK.value,
        )
        result = api.get_latest(tags=tags)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/latest/{URI}'
        assert result.records is None
        assert result.content is not None

    @responses.activate
    def test_get_latest_multiple(self, api: APIClient) -> None:
        tags = ['log']
        responses.add(
            method=responses.GET,
            url=f'{api.addr}/latest/{URI}',
            status=HTTPStatus.OK.value,
            content_type='application/json',
            json=[
                {
                    "ref": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "tags": ["log", "mothership"],
                    "created": "2020-10-29T00:38:50+00:00"
                },
                {
                    "ref": "f112be06fe41be15394ffe5d35eac60a9463674995b40c666b6febabe3942a42",
                    "tags": ["development", "log"],
                    "created": "2020-10-29T00:38:23+00:00"
                },
            ],
        )
        result = api.get_latest(tags=tags)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/latest/{URI}'
        assert result.content is None
        assert len(result.records) == 2
        assert result.records[0].ref == \
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        assert result.records[0].tags == set(['log', 'mothership'])
        assert result.records[0].created == datetime.datetime(
            2020, 10, 29, 00, 38, 50, tzinfo=datetime.timezone.utc)
        assert result.records[1].ref == \
            'f112be06fe41be15394ffe5d35eac60a9463674995b40c666b6febabe3942a42'
        assert result.records[1].tags == set(['development', 'log'])
        assert result.records[1].created == datetime.datetime(
            2020, 10, 29, 00, 38, 23, tzinfo=datetime.timezone.utc)

    @responses.activate
    def test_get_history(self, api: APIClient) -> None:
        tags = ['log', 'development']
        responses.add(
            method=responses.GET,
            url=f'{api.addr}/history/{URI}',
            status=HTTPStatus.OK.value,
            content_type='application/json',
            json=[
                {
                    "ref": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "tags": ["development", "log", "mothership"],
                    "created": "2020-10-29T00:38:50+00:00"
                },
                {
                    "ref": "f112be06fe41be15394ffe5d35eac60a9463674995b40c666b6febabe3942a42",
                    "tags": ["development", "log", "mothership"],
                    "created": "2020-10-29T00:38:23+00:00"
                },
            ],
        )
        records = api.get_history(tags=tags)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/latest/{URI}'
        assert len(records) == 2
        assert records[0].ref == \
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        assert records[0].tags == set(['development', 'log', 'mothership'])
        assert records[0].created == datetime.datetime(
            2020, 10, 29, 00, 38, 50, tzinfo=datetime.timezone.utc)
        assert records[1].ref == \
            'f112be06fe41be15394ffe5d35eac60a9463674995b40c666b6febabe3942a42'
        assert records[1].tags == set(['development', 'log', 'mothership'])
        assert records[1].created == datetime.datetime(
            2020, 10, 29, 00, 38, 23, tzinfo=datetime.timezone.utc)

    @responses.activate
    def test_delete_history(self, api: APIClient) -> None:
        tags = ['log', 'development']
        responses.add(
            method=responses.DELETE,
            url=f'{api.addr}/history/{URI}',
            status=HTTPStatus.NO_CONTENT.value,
        )
        api.delete_history(tags=tags)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/history/{URI}'
