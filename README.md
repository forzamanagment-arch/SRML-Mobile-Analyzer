# SRML Mobile Metadata Analyzer

Early research tool for inspecting Unity IL2CPP binaries used by Slime Rancher Mobile.

## Status

**Early v0.3 research build.** The tool validates the v39 metadata header, decodes the ordinary string pool and string literals, and now has bounded decoders for image and assembly records. It still does not produce a complete IL2CPP dump. All record decoders need validation against the target game's local metadata file.

## Target sample

- Unity: 6000.3.0f1
- Metadata version observed: 39
- Native library: ELF64, little-endian, AArch64
- Android ABI: arm64-v8a

Game binaries are not stored in this repository. Keep `global-metadata.dat` and `libil2cpp.so` local.

## Requirements

- Python 3.10+

## Usage

```bash
python -m srml_analyzer inspect-metadata global-metadata.dat
python -m srml_analyzer inspect-elf libil2cpp.so
python -m srml_analyzer inspect-pair global-metadata.dat libil2cpp.so
python -m srml_analyzer dump-strings global-metadata.dat --limit 200 --pretty
python -m srml_analyzer dump-literals global-metadata.dat --limit 200 --pretty
python -m srml_analyzer dump-images global-metadata.dat --limit 200 --pretty
python -m srml_analyzer dump-assemblies global-metadata.dat --limit 200 --pretty
python -m srml_analyzer dump-types global-metadata.dat --limit 200 --pretty
python -m srml_analyzer dump-fields global-metadata.dat --limit 200 --pretty
python -m srml_analyzer dump-methods global-metadata.dat --limit 200 --pretty
python -m srml_analyzer dump-parameters global-metadata.dat --limit 200 --pretty
```

Add `--pretty` for formatted JSON. `dump-strings` decodes the ordinary v39 UTF-8 string blob, `dump-literals` decodes the separate string-literal table, and `dump-images` / `dump-assemblies` decode their corresponding v39 records; `dump-types`, `dump-fields`, `dump-methods`, and `dump-parameters` decode the core type/member records. Names are resolved through the ordinary string pool. Each dump prints up to 100 entries by default; use `--limit` to change the preview size.

For metadata v39, `inspect-metadata` reports the parsed header sections and calculated index widths. For other versions, it only checks the magic/version prefix and labels any offset/size scan as exploratory.

## Development

```bash
python -m unittest discover -s tests -v
```

## Roadmap

1. Validate the v39 header against the target game's local sample.
2. Validate all current v39 table decoders against the target sample; then add relationships, generic metadata, and cross-table reference checks.
3. Resolve method pointers using the matching ELF and registration structures.
4. Export stable JSON and human-readable dumps.

No game binaries should be committed to this public repository.
