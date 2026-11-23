"""Command-line interface."""
from __future__ import annotations

import argparse
import json
import sys
from .errors import AnalyzerError
from .metadata import inspect_metadata
from .elf import inspect_elf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="srml-analyzer")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect-metadata", "inspect-elf"):
        cmd = sub.add_parser(name)
        cmd.add_argument("file")
        cmd.add_argument("--pretty", action="store_true")
    pair = sub.add_parser("inspect-pair")
    pair.add_argument("metadata")
    pair.add_argument("elf")
    pair.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect-metadata":
            result = inspect_metadata(args.file)
        elif args.command == "inspect-elf":
            result = inspect_elf(args.file)
        else:
            result = {
                "metadata": inspect_metadata(args.metadata),
                "native_library": inspect_elf(args.elf),
                "pairing": {
                    "metadata_version": 39,
                    "native_architecture": "AArch64",
                    "compatibility_verified": False,
                    "note": "Matching runtime registration structures are not decoded yet.",
                },
            }
        print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
        return 0
    except (AnalyzerError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
