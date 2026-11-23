# Format research notes

## Confirmed observations from the target sample

- Metadata magic bytes: `AF 1B B1 FA`.
- Metadata version field: little-endian uint32 value `39`.
- Unity engine version reported by the sample: `6000.3.0f1`.
- Native library target: ELF64 little-endian, AArch64 / arm64-v8a.

These observations identify the target family, but do not by themselves validate every table definition.

## Unity 6000.3 metadata v38/v39 research

The reviewed Unity 6000.3-era Il2CppDumper changes describe a v38+ global metadata header containing section offset/size/count triples. Version-gated legacy fields are absent in v39. The reference implementation also derives array lengths from explicit counts for fixed-record tables and uses variable-width serialized indices.

Reference material:
- [Il2CppDumper Unity 6 support PR #922](https://github.com/Perfare/Il2CppDumper/pull/922)
- [PR file changes](https://github.com/Perfare/Il2CppDumper/pull/922/files)

The project now contains `srml_analyzer/v39_header.py`, which:
- Parses the v39 header field sequence (currently 380 bytes).
- Exposes 31 named section descriptors with offset, byte size, count, and end.
- Rejects truncated headers and section ranges outside the input file.
- Computes the four variable index widths from header counts and record-size relationships.

Index width rules implemented in `srml_analyzer/index_widths.py`:
- Type-definition indices: width derived from type-definition count.
- Generic-container indices: width derived from generic-container count.
- Parameter-definition indices: variable-width in v39.
- Type indices: inferred from interface-offset record size when available, otherwise from field-record size, otherwise defaulting to 4 bytes.
- Widths are 1, 2, or 4 bytes. An all-ones value for the selected width is the null index sentinel (-1).
- Count-derived widths: counts up to 255 use 1 byte, up to 65,535 use 2 bytes, and larger counts use 4 bytes.

The v39 header parser is covered by synthetic tests. This is not yet proof that the schema matches the target game's actual file: the local `global-metadata.dat` has not yet been run through this parser in the project workflow.

## String pool decoder

The v39 `strings` section is a shared UTF-8 byte blob. Name indices are byte offsets into this blob, and strings are NUL-terminated; they are not sequential table-record IDs. The separate `string_literals` table is not decoded by this feature. The reference implementation resolves ordinary names by adding the stored index to `stringOffset` and reading through the next NUL byte. For v35 and later, string-literal lengths are derived from adjacent literal data offsets rather than the legacy per-literal length field.

The analyzer now provides `dump-strings`, which scans the bounded string section, validates UTF-8 and terminators, preserves each string's byte offset, and emits a limited preview. The v39 header's `strings.count` field is reported but deliberately not treated as the number of NUL-separated entries until that field's semantics are independently confirmed.

### String-literal table

The v39 `string_literals` records contain a single 32-bit `dataIndex`; the legacy per-record `length` field is absent. The decoder validates the table size against the explicit record count, checks that data offsets are monotonic and bounded, and derives each UTF-8 literal's length from the next record or the end of `string_literal_data`. This follows the v38+ record definition and the v35+ length calculation in the reviewed Il2CppDumper implementation. It has synthetic tests only; the target game's sample has not yet been checked.

## Important limitations

- The v39 header parser validates header fields and section bounds; it does not decode table records.
- Image, assembly, type, field, method, and parameter records are not yet decoded. Both the ordinary v39 string blob and the separate string-literal table now have bounded decoders.
- The header schema is based on a reviewed reference implementation, not an independently published Unity specification.
- The ELF inspector validates the basic ELF64 little-endian header and ordinary program/section table bounds. Extended section numbering is not implemented. It does not parse dynamic symbols, relocations, or IL2CPP registration structures.
- No target-game binary is stored in this public repository.

## Next research target

Run the parser against the target game's local `global-metadata.dat` without committing the binary. Then implement and test v39 record decoders, starting with strings, images, assemblies, types, fields, methods, and parameters.
