# SRML Mobile Metadata Analyzer

Early research tool for inspecting Unity IL2CPP binaries used by Slime Rancher Mobile.

## Status

**Early v0.5 research build.** The Python analyzer validates the v39 metadata header and decodes strings, literals, images, assemblies, core class/member records, properties, events, generic metadata, and selected index arrays. `inspect-model` builds per-class summaries and checks cross-table ranges. A mobile-friendly browser analyzer is included under `web/`. Use the single-file `web/analyzer-offline.html` on Android: download it from the repository and open it in a browser. It reads the selected metadata file locally and exports JSON. The page contains no external scripts or upload requests. Synthetic fixtures and browser parser tests run in CI. The actual game sample has not yet been validated.

## Target sample

- Unity: 6000.3.0f1
- Metadata version observed: 39
- Native library: ELF64, little-endian, AArch64
- Android ABI: arm64-v8a

Game binaries are not stored in this repository. Keep `global-metadata.dat` and `libil2cpp.so` local.

## Requirements

- Python 3.10+ for the CLI.
- A modern browser for the offline mobile analyzer in `web/analyzer-offline.html`.

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

On Android, open [`web/analyzer-offline.html`](web/analyzer-offline.html) in a modern browser, select `global-metadata.dat`, and export the JSON report. This is a self-contained file, so it does not need hosting, Python, Termux, or an internet connection after download. Add `--pretty` for formatted JSON. `dump-strings` decodes the ordinary v39 UTF-8 string blob, `dump-literals` decodes the separate string-literal table, and `dump-images` / `dump-assemblies` decode their corresponding v39 records; `dump-types`, `dump-fields`, `dump-methods`, and `dump-parameters` decode the core type/member records. Names are resolved through the ordinary string pool. Each dump prints up to 100 entries by default; use `--limit` to change the preview size. `inspect-model` emits a compact cross-linked class model with fields, methods and parameters, properties, events, generic metadata, images, assemblies, and validation warnings/errors. `TypeIndex` references are decoded structurally but their names require the matching native registration data from `libil2cpp.so`.

For metadata v39, `inspect-metadata` reports the parsed header sections and calculated index widths. For other versions, it only checks the magic/version prefix and labels any offset/size scan as exploratory.

## Research documents

- [Custom slime creation research](docs/SLIME_CREATION_RESEARCH.md)
- [Target slime registration metadata v39 findings](docs/TARGET_SLIME_REGISTRATION_METADATA_V39_2026-11-24.md)
- [Addon package format](docs/ADDON_FORMAT.md)
- [Android loader and Manager bootstrap research](docs/LOADER_BOOTSTRAP_RESEARCH.md)

## Development

```bash
python -m unittest discover -s tests -v
```

## Roadmap

1. Validate the v39 header against the target game's local sample.
2. Run `inspect-model` on the target game's local `global-metadata.dat` and fix any layout mismatches.
3. Use the target metadata file with the browser or CLI analyzer and fix any real-sample mismatches.
4. Resolve `TypeIndex` references and method pointers using the matching `libil2cpp.so` metadata/code registration structures.
5. Export stable JSON and human-readable reports, then begin game-class analysis.

No game binaries should be committed to this public repository.
