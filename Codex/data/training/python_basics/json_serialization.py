"""JSON serialization and deserialization examples."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass
class Event:
    name: str
    value: int


def serialize(event: Event) -> str:
    return json.dumps(asdict(event))


def deserialize(payload: str) -> Event:
    data = json.loads(payload)
    return Event(**data)


def main() -> None:
    payload = serialize(Event("ping", 1))
    print(payload)
    print(deserialize(payload))


if __name__ == "__main__":
    main()
