"""Additional bounded v39 metadata table decoders."""
from __future__ import annotations

import struct

from .core_tables import _index, _table, _strings
from .errors import FormatError
from .images_assemblies import _read_name


def decode_properties(data: bytes, header: dict) -> list[dict]:
    blob, count = _table(data, header, "properties", 20)
    strings = _strings(data, header)
    out = []
    for i in range(count):
        pos = i * 20
        name_index, getter, setter, attrs, token = struct.unpack_from("<IiiII", blob, pos)
        out.append({
            "index": i,
            "name": _read_name(strings, name_index, f"property[{i}]"),
            "name_index": name_index,
            "getter_method": getter,
            "setter_method": setter,
            "attributes": attrs,
            "token": token,
        })
    return out


def decode_events(data: bytes, header: dict) -> list[dict]:
    width = header["index_widths"]["type_index"]
    blob, count = _table(data, header, "events", 20 + width)
    strings = _strings(data, header)
    out = []
    pos = 0
    for i in range(count):
        name_index = struct.unpack_from("<I", blob, pos)[0]
        pos += 4
        type_index = _index(blob, pos, width)
        pos += width
        add, remove, raise_, token = struct.unpack_from("<iiiI", blob, pos)
        pos += 16
        out.append({
            "index": i,
            "name": _read_name(strings, name_index, f"event[{i}]"),
            "name_index": name_index,
            "type_index": type_index,
            "add_method": add,
            "remove_method": remove,
            "raise_method": raise_,
            "token": token,
        })
    return out


def decode_generic_containers(data: bytes, header: dict) -> list[dict]:
    blob, count = _table(data, header, "generic_containers", 16)
    out = []
    for i in range(count):
        owner, arity, is_method, parameter_start = struct.unpack_from("<4i", blob, i * 16)
        out.append({
            "index": i,
            "owner_index": owner,
            "type_argument_count": arity,
            "is_method": bool(is_method),
            "generic_parameter_start": parameter_start,
        })
    return out


def decode_generic_parameters(data: bytes, header: dict) -> list[dict]:
    width = header["index_widths"]["generic_container_index"]
    blob, count = _table(data, header, "generic_parameters", 12 + width)
    strings = _strings(data, header)
    out = []
    pos = 0
    for i in range(count):
        owner = _index(blob, pos, width)
        pos += width
        name_index = struct.unpack_from("<I", blob, pos)[0]
        pos += 4
        constraints_start, constraints_count, number, flags = struct.unpack_from("<hhHH", blob, pos)
        pos += 8
        out.append({
            "index": i,
            "owner_index": owner,
            "name": _read_name(strings, name_index, f"generic_parameter[{i}]"),
            "name_index": name_index,
            "constraints_start": constraints_start,
            "constraints_count": constraints_count,
            "number": number,
            "flags": flags,
        })
    return out


def decode_variable_index_array(data: bytes, header: dict, section_name: str, width_name: str) -> list[int]:
    section = header["sections"][section_name]
    width = header["index_widths"][width_name]
    expected = section["count"] * width
    if section["size"] != expected:
        raise FormatError(
            f"Invalid v39 {section_name} array size: expected {expected} "
            f"({section['count']} x {width}), got {section['size']}."
        )
    blob = data[section["offset"]:section["end"]]
    return [_index(blob, i * width, width) for i in range(section["count"])]


def decode_fixed_i32_array(data: bytes, header: dict, section_name: str) -> list[int]:
    section = header["sections"][section_name]
    expected = section["count"] * 4
    if section["size"] != expected:
        raise FormatError(
            f"Invalid v39 {section_name} array size: expected {expected} "
            f"({section['count']} x 4), got {section['size']}."
        )
    blob = data[section["offset"]:section["end"]]
    return list(struct.unpack(f"<{section['count']}i", blob)) if section["count"] else []


def decode_u32_array(data: bytes, header: dict, section_name: str) -> list[int]:
    section = header["sections"][section_name]
    expected = section["count"] * 4
    if section["size"] != expected:
        raise FormatError(
            f"Invalid v39 {section_name} array size: expected {expected} "
            f"({section['count']} x 4), got {section['size']}."
        )
    blob = data[section["offset"]:section["end"]]
    return list(struct.unpack(f"<{section['count']}I", blob)) if section["count"] else []


def decode_interface_offsets(data: bytes, header: dict) -> list[dict]:
    width = header["index_widths"]["type_index"]
    blob, count = _table(data, header, "interface_offsets", width + 4)
    out = []
    for i in range(count):
        pos = i * (width + 4)
        type_index = _index(blob, pos, width)
        offset = struct.unpack_from("<i", blob, pos + width)[0]
        out.append({"index": i, "type_index": type_index, "offset": offset})
    return out
