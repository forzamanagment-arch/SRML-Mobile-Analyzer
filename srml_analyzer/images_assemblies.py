"""Bounded v39 decoders for image and assembly records."""
from __future__ import annotations

import struct
from pathlib import Path

from .errors import FormatError
from .v39_header import parse_v39_header


def _read_name(strings: bytes, index: int, label: str) -> str:
    if index < 0 or index >= len(strings):
        raise FormatError(f"{label} string index {index} is outside the strings section.")
    end = strings.find(b"\\x00", index)
    if end < 0:
        raise FormatError(f"{label} string at offset {index} has no NUL terminator.")
    try:
        return strings[index:end].decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise FormatError(f"Invalid UTF-8 in {label} string at offset {index}: {exc}.") from exc


def _read_variable_index(data: bytes, offset: int, width: int) -> int:
    if width not in (1, 2, 4):
        raise FormatError(f"Unsupported variable index width: {width}.")
    raw = int.from_bytes(data[offset:offset + width], "little", signed=False)
    return -1 if raw == (1 << (width * 8)) - 1 else raw


def decode_images(data: bytes, header: dict) -> list[dict]:
    section = header["sections"]["images"]
    strings_section = header["sections"]["strings"]
    strings = data[strings_section["offset"]:strings_section["end"]]
    width = header["index_widths"]["type_definition_index"]
    record_size = 32 + 2 * width
    expected_size = section["count"] * record_size
    if section["size"] != expected_size:
        raise FormatError(
            f"Invalid v39 image table size: expected {expected_size} "
            f"({section['count']} x {record_size}), got {section['size']}."
        )

    result = []
    cursor = section["offset"]
    for i in range(section["count"]):
        name_index, assembly_index = struct.unpack_from("<Ii", data, cursor)
        cursor += 8
        type_start = _read_variable_index(data, cursor, width)
        cursor += width
        type_count = struct.unpack_from("<I", data, cursor)[0]
        cursor += 4
        exported_type_start = _read_variable_index(data, cursor, width)
        cursor += width
        exported_type_count, entry_point_index, token, custom_attribute_start, custom_attribute_count = struct.unpack_from(
            "<I i I i I", data, cursor
        )
        cursor += 20
        result.append({
            "index": i,
            "name": _read_name(strings, name_index, f"image[{i}]"),
            "name_index": name_index,
            "assembly_index": assembly_index,
            "type_start": type_start,
            "type_count": type_count,
            "exported_type_start": exported_type_start,
            "exported_type_count": exported_type_count,
            "entry_point_index": entry_point_index,
            "token": token,
            "custom_attribute_start": custom_attribute_start,
            "custom_attribute_count": custom_attribute_count,
        })
    return result


def decode_assemblies(data: bytes, header: dict) -> list[dict]:
    section = header["sections"]["assemblies"]
    strings_section = header["sections"]["strings"]
    strings = data[strings_section["offset"]:strings_section["end"]]
    record_size = 68
    expected_size = section["count"] * record_size
    if section["size"] != expected_size:
        raise FormatError(
            f"Invalid v39 assembly table size: expected {expected_size} "
            f"({section['count']} x {record_size}), got {section['size']}."
        )

    result = []
    cursor = section["offset"]
    for i in range(section["count"]):
        image_index, token, module_token, referenced_start, referenced_count = struct.unpack_from(
            "<iIIII", data, cursor
        )
        cursor += 20
        (
            name_index, culture_index, public_key_index, hash_alg, hash_len,
            flags, major, minor, build, revision,
        ) = struct.unpack_from("<10I", data, cursor)
        cursor += 40
        public_key_token = data[cursor:cursor + 8]
        cursor += 8
        result.append({
            "index": i,
            "image_index": image_index,
            "token": token,
            "module_token": module_token,
            "referenced_assembly_start": referenced_start,
            "referenced_assembly_count": referenced_count,
            "name": _read_name(strings, name_index, f"assembly[{i}] name"),
            "culture": _read_name(strings, culture_index, f"assembly[{i}] culture") if culture_index else "",
            "public_key_index": public_key_index,
            "hash_algorithm": hash_alg,
            "hash_length": hash_len,
            "flags": flags,
            "version": {"major": major, "minor": minor, "build": build, "revision": revision},
            "public_key_token": public_key_token.hex(),
        })
    return result


def inspect_images(path: str | Path, limit: int = 100) -> dict:
    if limit < 0:
        raise ValueError("limit must be zero or greater")
    data = Path(path).read_bytes()
    header = parse_v39_header(data)
    entries = decode_images(data, header)
    return {
        "format": "il2cpp-v39-images",
        "file": Path(path).name,
        "decoded_entries": len(entries),
        "entries": entries[:limit],
        "entries_omitted": max(0, len(entries) - limit),
    }


def inspect_assemblies(path: str | Path, limit: int = 100) -> dict:
    if limit < 0:
        raise ValueError("limit must be zero or greater")
    data = Path(path).read_bytes()
    header = parse_v39_header(data)
    entries = decode_assemblies(data, header)
    return {
        "format": "il2cpp-v39-assemblies",
        "file": Path(path).name,
        "decoded_entries": len(entries),
        "entries": entries[:limit],
        "entries_omitted": max(0, len(entries) - limit),
    }
