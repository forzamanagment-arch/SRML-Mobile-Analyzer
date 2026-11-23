"""Bounds-checked ELF64 little-endian container inspector."""
from __future__ import annotations

import struct
from pathlib import Path
from .errors import FormatError

ELF_MAGIC = b"\x7fELF"
EM_AARCH64 = 183


def inspect_elf(path: str | Path) -> dict:
    data = Path(path).read_bytes()
    if len(data) < 64:
        raise FormatError("File is too small to contain an ELF64 header.")
    if data[:4] != ELF_MAGIC:
        raise FormatError("Input does not have ELF magic.")

    elf_class, encoding, ident_version = data[4], data[5], data[6]
    if elf_class != 2:
        raise FormatError(f"Expected ELF64 (class 2), got class {elf_class}.")
    if encoding != 1:
        raise FormatError(f"Expected little-endian ELF (encoding 1), got {encoding}.")
    if ident_version != 1:
        raise FormatError(f"Unsupported ELF identification version: {ident_version}.")

    header = struct.unpack_from("<HHIQQQIHHHHHH", data, 16)
    e_type, machine, version, entry, phoff, shoff, flags, ehsize, phentsize, phnum, shentsize, shnum, shstrndx = header
    if ehsize < 64 or ehsize > len(data):
        raise FormatError(f"Invalid ELF header size: {ehsize}.")

    _check_table("program header", phoff, phentsize, phnum, len(data), 56)
    _check_table("section header", shoff, shentsize, shnum, len(data), 64)

    return {
        "format": "ELF64",
        "file": Path(path).name,
        "file_size": len(data),
        "class": elf_class,
        "endianness": "little",
        "type": e_type,
        "machine": machine,
        "machine_name": "AArch64" if machine == EM_AARCH64 else "unknown",
        "is_aarch64": machine == EM_AARCH64,
        "entry_point": entry,
        "program_header_offset": phoff,
        "program_header_entry_size": phentsize,
        "program_header_count": phnum,
        "section_header_offset": shoff,
        "section_header_entry_size": shentsize,
        "section_header_count": shnum,
        "extended_section_numbering_supported": False,
        "status": "container-validated",
    }


def _check_table(name: str, offset: int, entry_size: int, count: int,
                 file_size: int, minimum_entry_size: int) -> None:
    if count == 0:
        if offset != 0 and offset > file_size:
            raise FormatError(f"{name} offset is outside the file.")
        return
    if offset == 0 or entry_size < minimum_entry_size:
        raise FormatError(f"Invalid {name} table header.")
    end = offset + entry_size * count
    if end < offset or end > file_size:
        raise FormatError(f"{name} table extends beyond end of file.")
