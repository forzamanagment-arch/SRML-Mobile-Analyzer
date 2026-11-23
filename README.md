# SRML Mobile Metadata Analyzer

Early research tool for inspecting Unity IL2CPP binaries used by Slime Rancher Mobile.

## Status

**Early v0.2 research build.** The tool validates the v39 metadata header structure and section ranges, calculates variable-width index sizes, and inspects ELF64 containers. It does not yet decode IL2CPP table records or produce a complete dump. The v39 parser still needs validation against the target game's local metadata file.

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
```

Add `--pretty` for formatted JSON. `dump-strings` decodes the ordinary v39 UTF-8 string blob and prints up to 100 entries by default; use `--limit` to change the preview size. It does not decode the separate string-literal table yet.

For metadata v39, `inspect-metadata` reports the parsed header sections and calculated index widths. For other versions, it only checks the magic/version prefix and labels any offset/size scan as exploratory.

## Development

```bash
python -m unittest discover -s tests -v
```

## Roadmap

1. Validate the v39 header against the target game's local sample.
2. Decode string literals, images, assemblies, types, fields, methods, and parameters. The ordinary name string blob has an initial bounded decoder.
3. Resolve method pointers using the matching ELF and registration structures.
4. Export stable JSON and human-readable dumps.

No game binaries should be committed to this public repository.
