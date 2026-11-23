"""Bounded decoders for core Unity IL2CPP metadata v39 records.

Record layouts follow the v38/v39 definitions in Perfare/Il2CppDumper PR #922.
They are deliberately isolated from runtime pointer resolution.
"""
from __future__ import annotations

import struct
from pathlib import Path

from .errors import FormatError
from .images_assemblies import _read_name
from .v39_header import parse_v39_header


def _index(data: bytes, offset: int, width: int) -> int:
    if width not in (1, 2, 4) or offset < 0 or offset + width > len(data):
        raise FormatError("Invalid or truncated variable-width index.")
    value = int.from_bytes(data[offset:offset + width], "little")
    return -1 if value == (1 << (8 * width)) - 1 else value


def _table(data: bytes, header: dict, section_name: str, record_size: int):
    section = header["sections"][section_name]
    expected = section["count"] * record_size
    if section["size"] != expected:
        raise FormatError(
            f"Invalid v39 {section_name} table size: expected {expected} "
            f"({section['count']} x {record_size}), got {section['size']}."
        )
    return data[section["offset"]:section["end"]], section["count"]


def _strings(data: bytes, header: dict) -> bytes:
    s = header["sections"]["strings"]
    return data[s["offset"]:s["end"]]


def decode_fields(data: bytes, header: dict) -> list[dict]:
    w = header["index_widths"]["type_index"]
    blob, count = _table(data, header, "fields", 8 + w)
    strings = _strings(data, header)
    out = []
    pos = 0
    for i in range(count):
        name_index = struct.unpack_from("<I", blob, pos)[0]
        pos += 4
        type_index = _index(blob, pos, w)
        pos += w
        token = struct.unpack_from("<I", blob, pos)[0]
        pos += 4
        out.append({"index": i, "name": _read_name(strings, name_index, f"field[{i}]"),
                    "name_index": name_index, "type_index": type_index, "token": token})
    return out


def decode_parameters(data: bytes, header: dict) -> list[dict]:
    w = header["index_widths"]["type_index"]
    blob, count = _table(data, header, "parameters", 8 + w)
    strings = _strings(data, header)
    out = []
    pos = 0
    for i in range(count):
        name_index, token = struct.unpack_from("<II", blob, pos)
        pos += 8
        type_index = _index(blob, pos, w)
        pos += w
        out.append({"index": i, "name": _read_name(strings, name_index, f"parameter[{i}]"),
                    "name_index": name_index, "token": token, "type_index": type_index})
    return out


def decode_methods(data: bytes, header: dict) -> list[dict]:
    widths = header["index_widths"]
    td = widths["type_definition_index"]
    ty = widths["type_index"]
    pd = widths["parameter_definition_index"]
    gc = widths["generic_container_index"]
    record_size = 20 + td + ty + pd + gc
    blob, count = _table(data, header, "methods", record_size)
    strings = _strings(data, header)
    out = []
    pos = 0
    for i in range(count):
        name_index = struct.unpack_from("<I", blob, pos)[0]
        pos += 4
        declaring_type = _index(blob, pos, td); pos += td
        return_type = _index(blob, pos, ty); pos += ty
        return_parameter_token = struct.unpack_from("<I", blob, pos)[0]; pos += 4
        parameter_start = _index(blob, pos, pd); pos += pd
        generic_container = _index(blob, pos, gc); pos += gc
        token = struct.unpack_from("<I", blob, pos)[0]; pos += 4
        flags, iflags, slot, parameter_count = struct.unpack_from("<4H", blob, pos); pos += 8
        out.append({
            "index": i, "name": _read_name(strings, name_index, f"method[{i}]"),
            "name_index": name_index, "declaring_type": declaring_type,
            "return_type": return_type, "return_parameter_token": return_parameter_token,
            "parameter_start": parameter_start, "generic_container_index": generic_container,
            "token": token, "flags": flags, "iflags": iflags, "slot": slot,
            "parameter_count": parameter_count,
        })
    return out


def decode_types(data: bytes, header: dict) -> list[dict]:
    widths = header["index_widths"]
    ty = widths["type_index"]
    gc = widths["generic_container_index"]
    # v35+ removed elementTypeIndex; enum underlying type is parentIndex.
    record_size = 68 + 3 * ty + gc
    blob, count = _table(data, header, "type_definitions", record_size)
    strings = _strings(data, header)
    out = []
    pos = 0
    for i in range(count):
        name_index, namespace_index = struct.unpack_from("<II", blob, pos); pos += 8
        byval_type = _index(blob, pos, ty); pos += ty
        declaring_type = _index(blob, pos, ty); pos += ty
        parent_type = _index(blob, pos, ty); pos += ty
        generic_container = _index(blob, pos, gc); pos += gc
        flags = struct.unpack_from("<I", blob, pos)[0]; pos += 4
        starts = struct.unpack_from("<8i", blob, pos); pos += 32
        counts = struct.unpack_from("<8H", blob, pos); pos += 16
        bitfield, token = struct.unpack_from("<II", blob, pos); pos += 8
        out.append({
            "index": i, "name": _read_name(strings, name_index, f"type[{i}] name"),
            "namespace": _read_name(strings, namespace_index, f"type[{i}] namespace"),
            "name_index": name_index, "namespace_index": namespace_index,
            "byval_type_index": byval_type, "declaring_type_index": declaring_type,
            "parent_type_index": parent_type, "enum_underlying_type_index": parent_type,
            "generic_container_index": generic_container, "flags": flags,
            "field_start": starts[0], "method_start": starts[1],
            "event_start": starts[2], "property_start": starts[3],
            "nested_types_start": starts[4], "interfaces_start": starts[5],
            "vtable_start": starts[6], "interface_offsets_start": starts[7],
            "method_count": counts[0], "property_count": counts[1],
            "field_count": counts[2], "event_count": counts[3],
            "nested_type_count": counts[4], "vtable_count": counts[5],
            "interfaces_count": counts[6], "interface_offsets_count": counts[7],
            "bitfield": bitfield, "is_value_type": bool(bitfield & 1),
            "is_enum": bool(bitfield & 2), "token": token,
        })
    return out


def inspect_table(path: str | Path, table: str, limit: int = 100) -> dict:
    if limit < 0:
        raise ValueError("limit must be zero or greater")
    data = Path(path).read_bytes()
    header = parse_v39_header(data)
    decoders = {
        "types": decode_types, "fields": decode_fields,
        "methods": decode_methods, "parameters": decode_parameters,
    }
    entries = decoders[table](data, header)
    return {"format": f"il2cpp-v39-{table}", "file": Path(path).name,
            "decoded_entries": len(entries), "entries": entries[:limit],
            "entries_omitted": max(0, len(entries) - limit)}
