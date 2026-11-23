"""Decoder for the compact v39 IL2CPP string-literal table."""
from __future__ import annotations

import struct
from pathlib import Path

from .errors import FormatError
from .v39_header import parse_v39_header


def decode_string_literals(
    data: bytes,
    table_offset: int,
    table_size: int,
    count: int,
    data_offset: int,
    data_size: int,
) -> list[dict]:
    """Decode v39 literals whose table records contain one dataIndex each.

    Literal byte lengths are inferred from the next record's dataIndex, or
    from the end of the literal-data section for the final record.
    """
    for label, offset, size in (
        ("literal table", table_offset, table_size),
        ("literal data", data_offset, data_size),
    ):
        if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
            raise FormatError(f"String-literal {label} range exceeds metadata file.")

    if count < 0:
        raise FormatError("Negative string-literal count.")
    if table_size != count * 4:
        raise FormatError(
            f"Invalid v39 string-literal table size: expected {count * 4}, got {table_size}."
        )

    indices = [
        struct.unpack_from("<i", data, table_offset + i * 4)[0]
        for i in range(count)
    ]
    previous = 0
    for i, index in enumerate(indices):
        if index < previous or index < 0 or index > data_size:
            raise FormatError(
                f"Invalid string-literal dataIndex at record {i}: {index}."
            )
        previous = index

    blob = data[data_offset:data_offset + data_size]
    entries = []
    for i, start in enumerate(indices):
        end = indices[i + 1] if i + 1 < count else data_size
        try:
            value = blob[start:end].decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise FormatError(
                f"Invalid UTF-8 in string literal {i} at data offset {start}: {exc}."
            ) from exc
        entries.append({"index": i, "data_offset": start, "value": value})
    return entries


def inspect_string_literals(path: str | Path, limit: int = 100) -> dict:
    """Inspect the v39 string-literal table and return a bounded preview."""
    if limit < 0:
        raise ValueError("limit must be zero or greater")

    data = Path(path).read_bytes()
    header = parse_v39_header(data)
    table = header["sections"]["string_literals"]
    literal_data = header["sections"]["string_literal_data"]
    entries = decode_string_literals(
        data,
        table["offset"],
        table["size"],
        table["count"],
        literal_data["offset"],
        literal_data["size"],
    )
    return {
        "format": "il2cpp-v39-string-literals",
        "file": Path(path).name,
        "table_count": table["count"],
        "data_size": literal_data["size"],
        "decoded_entries": len(entries),
        "entries": entries[:limit],
        "entries_omitted": max(0, len(entries) - limit),
        "note": (
            "v39 literal records contain data offsets; byte lengths are inferred "
            "from the next record or the end of the literal-data section."
        ),
    }
