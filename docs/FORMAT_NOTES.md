# Format research notes

## Confirmed observations from the target sample

- Metadata magic bytes: `AF 1B B1 FA`.
- Metadata version field: little-endian uint32 value `39`.
- Unity engine version reported by the sample: `6000.3.0f1`.
- Native library target: ELF64 little-endian, AArch64 / arm64-v8a.

## Important limitations

The metadata inspector currently validates only the magic and version field. Its offset/size scanner is exploratory and may report false positives. It does not identify actual table types.

The ELF inspector validates the basic ELF64 little-endian header and ordinary program/section table bounds. Extended section numbering is not implemented. It does not parse dynamic symbols, relocations, or IL2CPP registration structures.

## Next research target

Verify the exact version-39 metadata header layout and table definitions against a known-good parser or a small independently inspected sample. Only after that should table offsets be given semantic names and decoded into records.
