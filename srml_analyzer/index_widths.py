"""Version-38/39 variable-width metadata index helpers.

This module implements the width rules observed in the Unity 6000.3-era
Il2CppDumper metadata definitions. It is intentionally not wired into the
file parser until the complete v39 header and record layouts are validated
against the target game's real metadata file.
"""
from __future__ import annotations

from dataclasses import dataclass

from .errors import FormatError


@dataclass(frozen=True)
class IndexWidths:
    type_index: int
    type_definition_index: int
    generic_container_index: int
    parameter_definition_index: int


def count_index_width(count: int) -> int:
    """Return serialized width for an index into a table of *count* entries."""
    if count < 0:
        raise FormatError(f"Negative metadata element count: {count}")
    if count <= 0xFF:
        return 1
    if count <= 0xFFFF:
        return 2
    return 4


def infer_type_index_width(
    interface_offsets_size: int,
    interface_offsets_count: int,
    fields_size: int,
    fields_count: int,
) -> int:
    """Infer TypeIndex width from record-size relationships.

    Interface-offset records contain a 32-bit offset plus a TypeIndex.
    Field records contain two 32-bit fields plus a TypeIndex.
    """
    if interface_offsets_count < 0 or fields_count < 0:
        raise FormatError("Metadata record counts cannot be negative.")
    if interface_offsets_size < 0 or fields_size < 0:
        raise FormatError("Metadata section sizes cannot be negative.")

    if interface_offsets_count:
        if interface_offsets_size % interface_offsets_count:
            raise FormatError("Interface-offset section size is not divisible by its count.")
        width = interface_offsets_size // interface_offsets_count - 4
    elif fields_count:
        if fields_size % fields_count:
            raise FormatError("Fields section size is not divisible by its count.")
        width = fields_size // fields_count - 8
    else:
        width = 4

    if width not in (1, 2, 4):
        raise FormatError(f"Inferred invalid TypeIndex width: {width}")
    return width


def derive_v39_index_widths(
    *,
    type_definitions_count: int,
    generic_containers_count: int,
    parameters_count: int,
    interface_offsets_size: int,
    interface_offsets_count: int,
    fields_size: int,
    fields_count: int,
) -> IndexWidths:
    return IndexWidths(
        type_index=infer_type_index_width(
            interface_offsets_size,
            interface_offsets_count,
            fields_size,
            fields_count,
        ),
        type_definition_index=count_index_width(type_definitions_count),
        generic_container_index=count_index_width(generic_containers_count),
        parameter_definition_index=count_index_width(parameters_count),
    )


def decode_variable_index(data: bytes, offset: int, width: int) -> int:
    """Decode a little-endian 1/2/4-byte index; all-ones is the null sentinel."""
    if width not in (1, 2, 4):
        raise FormatError(f"Unsupported variable index width: {width}")
    if offset < 0 or offset + width > len(data):
        raise FormatError("Variable index extends beyond the supplied data.")
    value = int.from_bytes(data[offset:offset + width], "little", signed=False)
    if value == (1 << (width * 8)) - 1:
        return -1
    return value
