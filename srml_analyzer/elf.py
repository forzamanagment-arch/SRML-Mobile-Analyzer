"""Bounds-checked ELF64 little-endian inspector with symbol discovery."""
from __future__ import annotations

import struct
from pathlib import Path

from .errors import FormatError

ELF_MAGIC = b"\x7fELF"
EM_AARCH64 = 183
SHT_SYMTAB = 2
SHT_STRTAB = 3
SHT_DYNSYM = 11
SHT_NOBITS = 8
SHN_XINDEX = 0xFFFF
PN_XNUM = 0xFFFF

INTERESTING_SYMBOL_PARTS = (
    "il2cpp", "metadataregistration", "coderegistration",
    "codegen_register", "g_MetadataRegistration", "g_CodeRegistration",
)


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


def _cstring(blob: bytes, offset: int, label: str) -> str:
    if offset < 0 or offset >= len(blob):
        if offset == 0:
            return ""
        raise FormatError(f"{label} string offset {offset} is outside its string table.")
    end = blob.find(b"\x00", offset)
    if end < 0:
        raise FormatError(f"{label} string at offset {offset} is not NUL-terminated.")
    return blob[offset:end].decode("utf-8", errors="replace")


def _section(data: bytes, offset: int, entry_size: int) -> dict:
    fields = struct.unpack_from("<IIQQQQIIQQ", data, offset)
    return {
        "name_offset": fields[0], "type": fields[1], "flags": fields[2],
        "address": fields[3], "offset": fields[4], "size": fields[5],
        "link": fields[6], "info": fields[7], "alignment": fields[8],
        "entry_size": fields[9],
    }


def _parse_symbols(data: bytes, sections: list[dict]) -> tuple[int, list[dict]]:
    total = 0
    found: list[dict] = []
    for section_index, section in enumerate(sections):
        if section["type"] not in (SHT_SYMTAB, SHT_DYNSYM):
            continue
        entry_size = section["entry_size"] or 24
        if entry_size < 24 or section["size"] % entry_size:
            raise FormatError(f"Invalid symbol table entry size in section {section_index}.")
        if section["link"] >= len(sections):
            raise FormatError(f"Symbol table section {section_index} has invalid string-table link.")
        strings_section = sections[section["link"]]
        strings = data[strings_section["offset"]:strings_section["offset"] + strings_section["size"]]
        count = section["size"] // entry_size
        total += count
        for i in range(count):
            pos = section["offset"] + i * entry_size
            name_offset, info, other, shndx, value, size = struct.unpack_from("<IBBHQQ", data, pos)
            name = _cstring(strings, name_offset, "ELF symbol")
            if not name or not any(part.lower() in name.lower() for part in INTERESTING_SYMBOL_PARTS):
                continue
            found.append({
                "name": name, "value": value, "size": size,
                "binding": info >> 4, "type": info & 0x0F,
                "section_index": shndx, "defined": shndx != 0,
                "table": "dynamic" if section["type"] == SHT_DYNSYM else "static",
            })
    found.sort(key=lambda item: (not item["defined"], item["name"]))
    return total, found[:500]


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
        raise FormatError(f"Expected little-endian ELF (encoding 1), got encoding {encoding}.")
    if ident_version != 1:
        raise FormatError(f"Unsupported ELF identification version: {ident_version}.")

    header = struct.unpack_from("<HHIQQQIHHHHHH", data, 16)
    e_type, machine, version, entry, phoff, shoff, flags, ehsize, phentsize, phnum, shentsize, shnum, shstrndx = header
    if ehsize < 64 or ehsize > len(data):
        raise FormatError(f"Invalid ELF header size: {ehsize}.")

    # Extended ELF numbering stores actual counts/indices in section header zero.
    section_zero = None
    if shoff and shentsize >= 64 and shoff + shentsize <= len(data):
        section_zero = _section(data, shoff, shentsize)
    if shnum == 0 and section_zero is not None:
        shnum = section_zero["size"]
    if shstrndx == SHN_XINDEX and section_zero is not None:
        shstrndx = section_zero["link"]
    if phnum == PN_XNUM and section_zero is not None:
        phnum = section_zero["info"]

    _check_table("program header", phoff, phentsize, phnum, len(data), 56)
    _check_table("section header", shoff, shentsize, shnum, len(data), 64)

    sections: list[dict] = []
    if shnum:
        for i in range(shnum):
            section = _section(data, shoff + i * shentsize, shentsize)
            if section["type"] != SHT_NOBITS:
                off, size = section["offset"], section["size"]
                if off > len(data) or size > len(data) - off:
                    raise FormatError(f"ELF section {i} extends beyond end of file.")
            sections.append(section)

    if sections and shstrndx < len(sections):
        names_section = sections[shstrndx]
        names_blob = data[names_section["offset"]:names_section["offset"] + names_section["size"]]
        for section in sections:
            section["name"] = _cstring(names_blob, section["name_offset"], "ELF section")
    else:
        for section in sections:
            section["name"] = ""

    symbol_count, interesting_symbols = _parse_symbols(data, sections) if sections else (0, [])
    named_sections = [
        {"name": s["name"], "type": s["type"], "offset": s["offset"], "size": s["size"]}
        for s in sections if s["name"]
    ]
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
        "extended_section_numbering_supported": True,
        "sections": named_sections[:300],
        "symbol_table_entries": symbol_count,
        "interesting_symbols": interesting_symbols,
        "symbol_note": (
            "Only symbols retained in ELF symbol tables can be discovered. "
            "Stripped local registration symbols may require code/relocation analysis."
        ),
        "status": "container-and-symbols-inspected",
    }
