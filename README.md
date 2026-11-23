# SRML Mobile Metadata Analyzer

Early research tool for inspecting Unity IL2CPP binaries used by Slime Rancher Mobile.

## Status

**v0.1 is a structural inspector, not a complete IL2CPP dumper.** It validates the metadata header and ELF64 container, then reports conservative offset/size candidates for manual format research. It does not yet decode type, method, field, image, or assembly records, and it does not claim complete support for metadata version 39.

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
```

Add `--pretty` for formatted JSON.

## Development

```bash
python -m unittest discover -s tests -v
```

## Roadmap

1. Validate metadata header and ELF container safely.
2. Confirm the exact v39 metadata header/table schema against real samples.
3. Decode images, assemblies, types, fields, and methods.
4. Resolve method pointers using the matching ELF and registration structures.
5. Export stable JSON and human-readable dumps.

No output from the exploratory scanner should be treated as a decoded IL2CPP table until independently verified.
