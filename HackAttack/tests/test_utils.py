"""Stub tests for core utilities."""

import json
import tempfile

from HackAttack.core.utils import load_json_file


def test_load_json_file_round_trip():
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=True) as handle:
        payload = {"status": "ok"}
        json.dump(payload, handle)
        handle.flush()
        assert load_json_file(handle.name) == payload
