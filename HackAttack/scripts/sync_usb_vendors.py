#!/usr/bin/env python3
"""Sync USB-IF vendor IDs with the local vendor database.

Usage:
    python HackAttack/scripts/sync_usb_vendors.py

This will normalize HackAttack/docs/usbif.json field_vid values and
insert any missing vendor IDs into HackAttack/modules/vendor_database.json
while preserving existing ordering.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Tuple

USBIF_PATH = Path("HackAttack/docs/usbif.json")
VENDOR_DB_PATH = Path("HackAttack/modules/vendor_database.json")


def normalize_vid(value: str | int) -> str:
    if isinstance(value, int):
        vid_int = value
    else:
        cleaned = value.strip()
        base = 16 if cleaned.lower().startswith("0x") else 10
        vid_int = int(cleaned, base=base)
    return f"0x{vid_int:04x}"


def sort_key(name: str, vid: str) -> Tuple[str, str, str]:
    return (name.lower(), name, vid)


def insert_missing(
    existing: Iterable[Tuple[str, str]], missing: Iterable[Tuple[str, str]]
) -> list[Tuple[str, str]]:
    ordered = list(existing)
    for vid, name in missing:
        new_key = sort_key(name, vid)
        inserted = False
        for idx, (cur_vid, cur_name) in enumerate(ordered):
            if sort_key(cur_name, cur_vid) > new_key:
                ordered.insert(idx, (vid, name))
                inserted = True
                break
        if not inserted:
            ordered.append((vid, name))
    return ordered


def main() -> None:
    usbif_data = json.loads(USBIF_PATH.read_text())
    for entry in usbif_data:
        entry["field_vid"] = normalize_vid(entry["field_vid"])

    vendor_db = json.loads(VENDOR_DB_PATH.read_text())
    vendors = vendor_db["vendors"]

    missing = []
    for entry in usbif_data:
        vid = entry["field_vid"]
        if vid not in vendors:
            missing.append((vid, entry["name"]))

    if missing:
        ordered = insert_missing(vendors.items(), missing)
        vendor_db["vendors"] = dict(ordered)

    USBIF_PATH.write_text(json.dumps(usbif_data, indent=4, ensure_ascii=False) + "\n")
    VENDOR_DB_PATH.write_text(
        json.dumps(vendor_db, indent=4, ensure_ascii=False) + "\n"
    )


if __name__ == "__main__":
    main()
