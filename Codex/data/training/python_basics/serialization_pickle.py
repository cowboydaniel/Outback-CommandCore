"""Pickle serialization examples."""

from __future__ import annotations

import pickle
from dataclasses import dataclass


@dataclass
class Payload:
    name: str
    value: int


def pack(payload: Payload) -> bytes:
    return pickle.dumps(payload)


def unpack(blob: bytes) -> Payload:
    return pickle.loads(blob)


def main() -> None:
    blob = pack(Payload("sample", 3))
    print(unpack(blob))


if __name__ == "__main__":
    main()
