import datetime
import uuid
from hashlib import sha256
from io import BytesIO

import pytest
import responses
from http import HTTPStatus

from motherlib.client import APIClient


class TestAPIClient:

    @pytest.fixture()
    def api(self) -> 'APIClient':
        return APIClient(addr='http://api.mother.ship', resource_owner_uid='test_uid')

    @responses.activate
    def test_cas_get(self, api: APIClient) -> None:
        test_content = str.encode(str(uuid.uuid4()))
        test_ref = f'/u/{api.resource_owner_uid}/cas/' + sha256(test_content).hexdigest()
        responses.add(
            method=responses.GET,
            url=f'{api.addr}{test_ref}',
            status=HTTPStatus.NO_CONTENT.value,
            content_type='application/octet-stream',
            body=test_content,
        )
        content = api.cas_get(ref=test_ref)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}{test_ref}'
        assert content.read() == test_content

    @responses.activate
    def test_put_latest(self, api: APIClient) -> None:
        tags = ['log', 'development']
        content = str.encode(str(uuid.uuid4()))
        test_ref = sha256(content).hexdigest()
        URI = '/'.join(tags)
        responses.add(
            method=responses.PUT,
            url=f'{api.addr}/u/{api.resource_owner_uid}/latest/{URI}',
            headers={'Location': f'/u/{api.resource_owner_uid}/cas/{test_ref}'},
            status=HTTPStatus.NO_CONTENT.value,
        )
        ref = api.put_latest(tags=tags, content=content)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/u/test_uid/latest/{URI}'
        assert ref == test_ref

    @responses.activate
    def test_get_latest(self, api: APIClient) -> None:
        tags = ['log']
        URI = '/'.join(tags)
        responses.add(
            method=responses.GET,
            url=f'{api.addr}/u/{api.resource_owner_uid}/latest/{URI}',
            status=HTTPStatus.OK.value,
            content_type='application/json',
            json=[
                {
                    "ref": f"/u/{api.resource_owner_uid}/cas/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "tags": ["log", "mothership"],
                    "created": "2020-10-29T00:38:50+00:00"
                },
                {
                    "ref": f"/u/{api.resource_owner_uid}/cas/f112be06fe41be15394ffe5d35eac60a9463674995b40c666b6febabe3942a42",
                    "tags": ["log", "development"],
                    "created": "2020-10-29T00:38:23+00:00"
                },
            ],
        )
        records = api.get_latest(tags=tags)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/u/test_uid/latest/{URI}'
        assert len(records) == 2
        assert records[0].ref == \
            '/u/test_uid/cas/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        assert records[0].tags == ['log', 'mothership']
        assert records[0].created == datetime.datetime(
            2020, 10, 29, 00, 38, 50, tzinfo=datetime.timezone.utc)
        assert records[1].ref == \
            '/u/test_uid/cas/f112be06fe41be15394ffe5d35eac60a9463674995b40c666b6febabe3942a42'
        assert records[1].tags == ['log', 'development']
        assert records[1].created == datetime.datetime(
            2020, 10, 29, 00, 38, 23, tzinfo=datetime.timezone.utc)

    @responses.activate
    def test_get_history(self, api: APIClient) -> None:
        tags = ['log', 'development']
        URI = '/'.join(tags)
        responses.add(
            method=responses.GET,
            url=f'{api.addr}/u/{api.resource_owner_uid}/history/{URI}',
            status=HTTPStatus.OK.value,
            content_type='application/json',
            json=[
                {
                    "ref": f"/u/{api.resource_owner_uid}/cas/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "tags": ["log", "development", "mothership"],
                    "created": "2020-10-29T00:38:50+00:00"
                },
                {
                    "ref": f"/u/{api.resource_owner_uid}/cas/f112be06fe41be15394ffe5d35eac60a9463674995b40c666b6febabe3942a42",
                    "tags": ["log", "development", "mothership"],
                    "created": "2020-10-29T00:38:23+00:00"
                },
            ],
        )
        records = api.get_history(tags=tags)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/u/test_uid/history/{URI}'
        assert len(records) == 2
        assert records[0].ref == \
            '/u/test_uid/cas/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        assert records[0].tags == ['log', 'development', 'mothership']
        assert records[0].created == datetime.datetime(
            2020, 10, 29, 00, 38, 50, tzinfo=datetime.timezone.utc)
        assert records[1].ref == \
            '/u/test_uid/cas/f112be06fe41be15394ffe5d35eac60a9463674995b40c666b6febabe3942a42'
        assert records[1].tags == ['log', 'development', 'mothership']
        assert records[1].created == datetime.datetime(
            2020, 10, 29, 00, 38, 23, tzinfo=datetime.timezone.utc)

    @responses.activate
    def test_delete_history(self, api: APIClient) -> None:
        tags = ['log', 'development']
        URI = '/'.join(tags)
        responses.add(
            method=responses.DELETE,
            url=f'{api.addr}/u/{api.resource_owner_uid}/history/{URI}',
            status=HTTPStatus.NO_CONTENT.value,
        )
        api.delete_history(tags=tags)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/u/test_uid/history/{URI}'
