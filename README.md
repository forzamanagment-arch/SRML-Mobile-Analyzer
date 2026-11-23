# SRML Mobile Metadata Analyzer

Early research tool for inspecting Unity IL2CPP binaries used by Slime Rancher Mobile.

## Status

**Early v0.4 research build.** The tool validates the v39 metadata header and has bounded decoders for strings, literals, images, assemblies, types, fields, methods, parameters, properties, events, generic containers, generic parameters, and index arrays. `inspect-model` assembles these into per-class summaries and checks cross-table ranges. Synthetic fixtures are covered by CI; the actual game sample has not yet been run through the parser.

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
python -m srml_analyzer dump-properties global-metadata.dat --limit 200 --pretty
python -m srml_analyzer dump-events global-metadata.dat --limit 200 --pretty
python -m srml_analyzer dump-generic-containers global-metadata.dat --limit 200 --pretty
python -m srml_analyzer dump-generic-parameters global-metadata.dat --limit 200 --pretty
python -m srml_analyzer inspect-model global-metadata.dat --pretty
```

Add `--pretty` for formatted JSON. `dump-strings` decodes the ordinary v39 UTF-8 string blob, `dump-literals` decodes the separate string-literal table, and `dump-images` / `dump-assemblies` decode their corresponding v39 records; `dump-types`, `dump-fields`, `dump-methods`, and `dump-parameters` decode the core type/member records. Names are resolved through the ordinary string pool. Each dump prints up to 100 entries by default; use `--limit` to change the preview size. `inspect-model` emits a compact cross-linked class model with fields, methods and parameters, properties, events, generic metadata, images, assemblies, and validation warnings/errors. `TypeIndex` references are decoded structurally but their names require the matching native registration data from `libil2cpp.so`.

For metadata v39, `inspect-metadata` reports the parsed header sections and calculated index widths. For other versions, it only checks the magic/version prefix and labels any offset/size scan as exploratory.

## Development

```bash
python -m unittest discover -s tests -v
```

## Roadmap

1. Validate the v39 header against the target game's local sample.
2. Run `inspect-model` on the target game's local `global-metadata.dat` and fix any layout mismatches.
3. Resolve `TypeIndex` references and method pointers using the matching `libil2cpp.so` metadata/code registration structures.
4. Export stable JSON and human-readable reports, then begin game-class analysis.

No game binaries should be committed to this public repository.
