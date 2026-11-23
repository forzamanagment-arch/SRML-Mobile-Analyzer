"""Conservative parser for the IL2CPP global-metadata container header.

The current implementation deliberately does not assign semantic names to
header pairs. Version-39 table layout must be verified before decoding.
"""
from __future__ import annotations

import struct
from pathlib import Path
from .errors import FormatError

MAGIC = bytes.fromhex("AF 1B B1 FA")
HEADER_PREFIX_SIZE = 8


def inspect_metadata(path: str | Path, max_candidates: int = 64) -> dict:
    data = Path(path).read_bytes()
    if len(data) < HEADER_PREFIX_SIZE:
        raise FormatError("File is too small to contain an IL2CPP metadata header.")
    if data[:4] != MAGIC:
        raise FormatError(f"Unexpected metadata magic: {data[:4].hex(' ').upper()}")

    version = struct.unpack_from("<I", data, 4)[0]
    result = {
        "format": "il2cpp-global-metadata",
        "file": Path(path).name,
        "file_size": len(data),
        "magic": data[:4].hex(" ").upper(),
        "version": version,
        "header_bytes": len(data),
        "status": "header-recognized",
        "table_schema_decoded": False,
        "notes": [
            "Offset/size pairs below are exploratory candidates only.",
            "No candidate is asserted to be a real metadata table.",
        ],
        "exploratory_candidates": _scan_pairs(data, max_candidates),
    }
    if version != 39:
        result["notes"].append(
            "This sample is not metadata version 39; schema compatibility is unverified."
        )
    else:
        result["notes"].append(
            "Version 39 identified. Full version-39 table schema is not implemented yet."
        )
    return result


def _scan_pairs(data: bytes, limit: int) -> list[dict]:
    """Find bounded aligned u32 offset/size pairs without naming their meaning."""
    candidates = []
    # Metadata headers are sequences of 32-bit values. Scan conservatively.
    for pos in range(8, len(data) - 7, 4):
        offset, size = struct.unpack_from("<II", data, pos)
        if size == 0 or offset < 8:
            continue
        end = offset + size
        if end > len(data) or end < offset:
            continue
        if offset % 4 != 0:
            continue
        candidates.append({
            "header_position": pos,
            "offset": offset,
            "size": size,
            "end": end,
        })
        if len(candidates) >= limit:
            break
    return candidates
