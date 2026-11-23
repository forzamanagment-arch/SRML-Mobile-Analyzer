# Format research notes

## Confirmed observations from the target sample

- Metadata magic bytes: `AF 1B B1 FA`.
- Metadata version field: little-endian uint32 value `39`.
- Unity engine version reported by the sample: `6000.3.0f1`.
- Native library target: ELF64 little-endian, AArch64 / arm64-v8a.

These observations identify the target family, but do not by themselves validate every table definition.

## Unity 6000.3 metadata v38/v39 research

The reviewed Unity 6000.3-era metadata definitions add explicit element counts alongside many section offset/size pairs. The reference parser uses these counts for record-array lengths instead of deriving every count from a fixed record size.

It also uses variable-width serialized indices:

- Type-definition indices: width derived from type-definition count.
- Generic-container indices: width derived from generic-container count.
- Parameter-definition indices: variable-width in v39.
- Type indices: inferred from interface-offset record size when available, otherwise from field-record size, otherwise defaulting to 4 bytes.
- Widths are 1, 2, or 4 bytes. An all-ones value for the selected width is the null index sentinel (-1).

For count-derived widths: counts up to 255 use 1 byte, up to 65,535 use 2 bytes, and larger counts use 4 bytes.

The project implements these calculations in `srml_analyzer/index_widths.py` with synthetic unit tests. This is a focused format-research component, not yet an end-to-end v39 parser.

## Important limitations

The metadata inspector currently validates only the magic and version field. Its offset/size scanner is exploratory and may report false positives. It does not identify actual table types or parse the complete v39 header.

The ELF inspector validates the basic ELF64 little-endian header and ordinary program/section table bounds. Extended section numbering is not implemented. It does not parse dynamic symbols, relocations, or IL2CPP registration structures.

## Next research target

Validate the complete v39 header and record layouts against the target game's real `global-metadata.dat`. Then decode images, assemblies, types, fields, methods, and parameters using count-based array lengths and the correct per-kind index widths.
