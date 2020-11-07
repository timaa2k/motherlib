from io import BytesIO
from typing import Any, Dict, List, Optional

import iso8601
import json


class Record:

    def __init__(
        self,
        tags: List[str] = None,
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
            tags=json['tags'],
            ref=json['ref'],
            created=json['created'],
        )
