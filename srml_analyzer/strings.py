"""Bounded decoder for the v39 metadata string blob.

Metadata string indices are byte offsets into the shared UTF-8 string blob.
They are not record numbers. String literals are a separate table and are
intentionally not decoded by this module.
"""
from __future__ import annotations

from pathlib import Path

from .errors import FormatError
from .v39_header import parse_v39_header


def decode_string_pool(data: bytes, offset: int, size: int) -> list[dict]:
    """Decode NUL-terminated UTF-8 strings from one already-bounded section.

    Returned offsets are relative to the beginning of the string section,
    matching the offsets stored in IL2CPP nameIndex fields.
    """
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise FormatError("String section range exceeds metadata file.")

    blob = data[offset:offset + size]
    if not blob:
        return []
    if blob[-1] != 0:
        raise FormatError("Metadata string section is not NUL-terminated.")

    entries = []
    cursor = 0
    for raw in blob[:-1].split(b"\x00"):
        try:
            value = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise FormatError(
                f"Invalid UTF-8 in metadata string at section offset {cursor}: {exc}."
            ) from exc
        entries.append({"offset": cursor, "value": value})
        cursor += len(raw) + 1
    return entries


def inspect_string_pool(path: str | Path, limit: int = 100) -> dict:
    """Inspect the v39 string blob and return a bounded preview."""
    if limit < 0:
        raise ValueError("limit must be zero or greater")

    data = Path(path).read_bytes()
    header = parse_v39_header(data)
    section = header["sections"]["strings"]
    entries = decode_string_pool(data, section["offset"], section["size"])
    return {
        "format": "il2cpp-v39-string-pool",
        "file": Path(path).name,
        "section_offset": section["offset"],
        "section_size": section["size"],
        "header_count_field": section["count"],
        "decoded_entries": len(entries),
        "count_field_matches_entries": section["count"] == len(entries),
        "entries": entries[:limit],
        "entries_omitted": max(0, len(entries) - limit),
        "note": (
            "String indices are byte offsets into this blob. The header count "
            "field is reported for research and is not assumed to be an entry count."
        ),
    }
