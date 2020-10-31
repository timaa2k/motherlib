from io import BytesIO
from typing import Any, Dict, List, Optional, Set

import iso8601
import json


class Record:

    def __init__(
        self,
        tags: Set[str] = None,
        ref: Optional[str] = None,
        created: Optional[str] = None,
    ) -> None:
        self.tags = tags
        self.ref = ref
        self.created = iso8601.parse_date(created) if created else None

    def __str__(self) -> str:
        return f'({self.ref}, {self.tags}, {self.created})'

    @classmethod
    def unmarshal_json(cls, json: Dict[str, Any]) -> 'Record':
        return cls(
            tags=set(list(json['tags'])),
            ref=json['ref'],
            created=json['created'],
        )


class Result:

    def __init(
        self,
        content: Optional[BytesIO] = None,
        records: Optional[List[Record]] = None,
    ) -> None:
        self.content = content
        self.records = records
