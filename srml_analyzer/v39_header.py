"""Validated Unity 6000.3 metadata v39 header reader.

The v39 header is a fixed sequence of 32-bit fields. Most sections carry
(offset, byte_size, element_count); a few legacy-only fields are absent.
This module parses only the header and validates section ranges. It does not
decode table records.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

from .errors import FormatError
from .index_widths import derive_v39_index_widths

MAGIC = bytes.fromhex("AF 1B B1 FA")
PREFIX_SIZE = 8

# Field order follows Il2CppGlobalMetadataHeader for metadata >= 38.
# Every entry is (section name, has explicit element count).
V39_SECTIONS = (
    ("string_literals", True),
    ("string_literal_data", True),
    ("strings", True),
    ("events", True),
    ("properties", True),
    ("methods", True),
    ("parameter_default_values", True),
    ("field_default_values", True),
    ("field_and_parameter_default_value_data", True),
    ("field_marshaled_sizes", True),
    ("parameters", True),
    ("fields", True),
    ("generic_parameters", True),
    ("generic_parameter_constraints", True),
    ("generic_containers", True),
    ("nested_types", True),
    ("interfaces", True),
    ("vtable_methods", True),
    ("interface_offsets", True),
    ("type_definitions", True),
    ("images", True),
    ("assemblies", True),
    ("field_refs", True),
    ("referenced_assemblies", True),
    ("attribute_data", True),
    ("attribute_data_ranges", True),
    ("unresolved_virtual_call_parameter_types", True),
    ("unresolved_virtual_call_parameter_ranges", True),
    ("windows_runtime_type_names", True),
    ("windows_runtime_strings", True),
    ("exported_type_definitions", True),
)


@dataclass(frozen=True)
class MetadataSection:
    name: str
    offset: int
    size: int
    count: int

    @property
    def end(self) -> int:
        return self.offset + self.size


def v39_header_size() -> int:
    return PREFIX_SIZE + sum(12 if has_count else 8 for _, has_count in V39_SECTIONS)


def parse_v39_header(data: bytes) -> dict:
    """Parse and validate the fixed v39 header and all section byte ranges."""
    if len(data) < PREFIX_SIZE:
        raise FormatError("Metadata file is too small for the header.")
    if data[:4] != MAGIC:
        raise FormatError(f"Unexpected metadata magic: {data[:4].hex(' ').upper()}")

    version = struct.unpack_from("<i", data, 4)[0]
    if version != 39:
        raise FormatError(f"Expected metadata version 39, got {version}.")

    expected_size = v39_header_size()
    if len(data) < expected_size:
        raise FormatError(
            f"Truncated v39 header: expected {expected_size} bytes, got {len(data)}."
        )

    sections = {}
    cursor = PREFIX_SIZE
    for name, has_count in V39_SECTIONS:
        offset, size = struct.unpack_from("<II", data, cursor)
        cursor += 8
        count = struct.unpack_from("<I", data, cursor)[0] if has_count else 0
        if has_count:
            cursor += 4

        # Values are serialized as 32-bit fields. Reject impossible ranges
        # before doing arithmetic or exposing them to later parsers.
        if offset == 0 and size == 0 and count == 0:
            section = MetadataSection(name, 0, 0, 0)
        else:
            if offset < expected_size:
                raise FormatError(
                    f"Section {name} starts inside the v39 header: {offset}."
                )
            if size > len(data) or offset > len(data) - size:
                raise FormatError(
                    f"Section {name} range [{offset}, {offset + size}) "
                    f"exceeds file size {len(data)}."
                )
            section = MetadataSection(name, offset, size, count)
        sections[name] = section

    if cursor != expected_size:
        raise FormatError("Internal v39 header schema length mismatch.")

    fields = sections["fields"]
    interfaces = sections["interface_offsets"]
    widths = derive_v39_index_widths(
        type_definitions_count=sections["type_definitions"].count,
        generic_containers_count=sections["generic_containers"].count,
        parameters_count=sections["parameters"].count,
        interface_offsets_size=interfaces.size,
        interface_offsets_count=interfaces.count,
        fields_size=fields.size,
        fields_count=fields.count,
    )

    return {
        "version": version,
        "header_size": expected_size,
        "sections": {
            name: {
                "offset": section.offset,
                "size": section.size,
                "count": section.count,
                "end": section.end,
            }
            for name, section in sections.items()
        },
        "index_widths": {
            "type_index": widths.type_index,
            "type_definition_index": widths.type_definition_index,
            "generic_container_index": widths.generic_container_index,
            "parameter_definition_index": widths.parameter_definition_index,
        },
    }
