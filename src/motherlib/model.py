from io import BytesIO
from typing import Any, Dict, List, Optional

import iso8601
import json


class AuthInfo:

    def __init__(
        self,
        provider: str,
        provider_name: str,
        auth_url: str,
    ) -> None:
        self.provider=provider
        self.provider_name=provider_name,
        self.auth_url=auth_url,

    def __str__(self) -> str:
        return f'({self.provider}, {self.provider_name}, {self.auth_url})'

    @classmethod
    def unmarshal_json(cls, json: Dict[str, Any]) -> 'AuthInfo':
        return cls(
            provider=json['provider'],
            provider_name=json['provider_name'],
            auth_url=json['auth_url'],
        )

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
