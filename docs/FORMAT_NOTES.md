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

The v39 `strings` section is a shared UTF-8 byte blob. Name indices are byte offsets into this blob, and strings are NUL-terminated; they are not sequential table-record IDs. The separate `string_literals` table uses its own data-index records. The reference implementation resolves ordinary names by adding the stored index to `stringOffset` and reading through the next NUL byte. For v35 and later, string-literal lengths are derived from adjacent literal data offsets rather than the legacy per-literal length field.

The analyzer provides `dump-strings`, which scans the bounded string section, validates UTF-8 and terminators, preserves each string's byte offset, and emits a limited preview. Image and assembly names are resolved directly by byte offset through the same bounded string blob. The v39 header's `strings.count` field is reported but deliberately not treated as the number of NUL-separated entries until that field's semantics are independently confirmed.

### String-literal table

The v39 `string_literals` records contain a single 32-bit `dataIndex`; the legacy per-record `length` field is absent. The decoder validates the table size against the explicit record count, checks that data offsets are monotonic and bounded, and derives each UTF-8 literal's length from the next record or the end of `string_literal_data`. This follows the v38+ record definition and the v35+ length calculation in the reviewed Il2CppDumper implementation. It has synthetic tests only; the target game's sample has not yet been checked.

### Image and assembly records

The v39 image decoder reads the version-appropriate image record, including variable-width type-definition indices, and resolves the image name through the shared string pool. The assembly decoder reads the v38+ assembly record, including the added module token and assembly-name fields, then resolves its name and culture strings. Both decoders validate that the declared table byte size exactly matches the expected record count and record size. Synthetic tests cover name resolution, fields, and malformed table sizes; target-game validation is still pending.

## Important limitations

- The v39 header parser validates header fields and section bounds. Bounded decoders cover image, assembly, type, field, method, parameter, property, event, generic-container, generic-parameter, interface-offset, and selected index-array records.
- String, string-literal, image, assembly, type, field, method, and parameter decoders currently have synthetic tests only. The target game's actual metadata file has not yet been processed by the project workflow.
- The header schema is based on a reviewed reference implementation, not an independently published Unity specification.
- The ELF inspector validates ELF64 little-endian headers, ordinary and extended section numbering, section bounds, and retained static/dynamic symbol tables. It highlights retained IL2CPP-related symbols. It does not yet parse relocations or reconstruct IL2CPP code/metadata registration structures.
- No target-game binary is stored in this public repository.

### Core type and member records

The v39 type-definition decoder reads compact TypeIndex and GenericContainerIndex values, the fixed member-range/count fields, flags, bitfield, and token. For v35+, the former element-type field is absent; the enum underlying type is represented by the parent type index. Field and parameter records use compact TypeIndex values. Method records use compact type-definition, type, parameter-definition, and generic-container indices. All four decoders validate exact table sizes and resolve names through the bounded string pool. The layouts follow the reviewed v38/v39 record definitions in Perfare/Il2CppDumper PR #922. They have synthetic fixtures only and are not yet validated against the target game.

## Integrated model and offline browser analyzer

`srml_analyzer/model.py` joins classes with their fields, methods, parameters, properties, and events. It validates member ranges, nested-type references, image/assembly links, and generic-container ranges. `TypeIndex` values are not class-definition indices; their names require the runtime type array reconstructed from the matching native library's metadata registration.

`srml_analyzer/extra_tables.py` decodes v39 properties, events, generic containers, generic parameters, interface offsets, and compact index arrays. The command `inspect-model` exports a cross-linked JSON report.

The `web/analyzer-offline.html` file is a self-contained browser tool for Android. It reads a user-selected metadata file with the browser File API, renders a class/member preview, and exports JSON. Its JavaScript is bundled in the HTML file; the offline smoke test checks script syntax and guards against network upload APIs. The modular `web/index.html` + `web/analyzer.js` variant is also retained for static hosting.

## Next research target

Run the parser against the target game's local `global-metadata.dat` without committing the binary. Then use the paired `libil2cpp.so` to resolve TypeIndex values and inspect code/metadata registration and method-pointer mappings.
