import json
import datetime

import motherlib.model


class TestRecord:

    def test_unmarshal_json(self) -> None:
        json = {}  # type = Dict[str, Any]
        json['tags'] = ['foo']
        json['ref'] = 'bar'
        json['created'] = '2007-01-25T12:00:00Z'
        r = motherlib.model.Record.unmarshal_json(json)
        assert r.tags == json['tags']
        assert r.ref == json['ref']
        assert r.created == datetime.datetime(
            2007, 1, 25, 12, 0, tzinfo=datetime.timezone.utc)
