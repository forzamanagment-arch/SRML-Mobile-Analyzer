"""Conservative parser for the IL2CPP global-metadata container header."""
from __future__ import annotations

import struct
from pathlib import Path

from .errors import FormatError
from .v39_header import MAGIC, PREFIX_SIZE, parse_v39_header

HEADER_PREFIX_SIZE = PREFIX_SIZE


def inspect_metadata(path: str | Path, max_candidates: int = 64) -> dict:
    data = Path(path).read_bytes()
    if len(data) < HEADER_PREFIX_SIZE:
        raise FormatError("File is too small to contain an IL2CPP metadata header.")
    if data[:4] != MAGIC:
        raise FormatError(f"Unexpected metadata magic: {data[:4].hex(' ').upper()}")

    version = struct.unpack_from("<i", data, 4)[0]
    result = {
        "format": "il2cpp-global-metadata",
        "file": Path(path).name,
        "file_size": len(data),
        "magic": data[:4].hex(" ").upper(),
        "version": version,
        "status": "header-recognized",
        "table_records_decoded": False,
    }

    if version == 39:
        parsed = parse_v39_header(data)
        result.update({
            "status": "v39-header-validated",
            "header_bytes": parsed["header_size"],
            "sections": parsed["sections"],
            "index_widths": parsed["index_widths"],
            "notes": [
                "The v39 header and section bounds were parsed.",
                "Table records are not decoded yet; this is not a complete IL2CPP dump.",
                "Validate this schema against the target game's local metadata sample before relying on it.",
            ],
        })
    else:
        result.update({
            "header_bytes": len(data),
            "status": "header-recognized-unparsed",
            "notes": [
                "Only the magic and version prefix were checked for this metadata version.",
                "No table schema is asserted for this version.",
            ],
            "exploratory_candidates": _scan_pairs(data, max_candidates),
        })
    return result


def _scan_pairs(data: bytes, limit: int) -> list[dict]:
    """Find bounded aligned u32 offset/size pairs without naming their meaning."""
    candidates = []
    for pos in range(8, len(data) - 7, 4):
        offset, size = struct.unpack_from("<II", data, pos)
        if size == 0 or offset < 8:
            continue
        end = offset + size
        if end > len(data) or end < offset or offset % 4:
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
