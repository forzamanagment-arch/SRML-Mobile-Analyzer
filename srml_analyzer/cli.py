"""Command-line interface."""
from __future__ import annotations

import argparse
import json
import sys

from .errors import AnalyzerError
from .metadata import inspect_metadata
from .elf import inspect_elf
from .strings import inspect_string_pool
from .string_literals import inspect_string_literals
from .images_assemblies import inspect_images, inspect_assemblies
from .core_tables import inspect_table
from .model import inspect_model


def nonnegative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="srml-analyzer")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect-metadata", "inspect-elf"):
        cmd = sub.add_parser(name)
        cmd.add_argument("file")
        cmd.add_argument("--pretty", action="store_true")

    strings = sub.add_parser("dump-strings")
    strings.add_argument("file")
    strings.add_argument("--limit", type=nonnegative_int, default=100)
    strings.add_argument("--pretty", action="store_true")

    literals = sub.add_parser("dump-literals")
    literals.add_argument("file")
    literals.add_argument("--limit", type=nonnegative_int, default=100)
    literals.add_argument("--pretty", action="store_true")

    images = sub.add_parser("dump-images")
    images.add_argument("file")
    images.add_argument("--limit", type=nonnegative_int, default=100)
    images.add_argument("--pretty", action="store_true")

    assemblies = sub.add_parser("dump-assemblies")
    assemblies.add_argument("file")
    assemblies.add_argument("--limit", type=nonnegative_int, default=100)
    assemblies.add_argument("--pretty", action="store_true")

    for name in ("types", "fields", "methods", "parameters"):
        cmd = sub.add_parser(f"dump-{name}")
        cmd.add_argument("file")
        cmd.add_argument("--limit", type=nonnegative_int, default=100)
        cmd.add_argument("--pretty", action="store_true")

    model = sub.add_parser("inspect-model")
    model.add_argument("file")
    model.add_argument("--pretty", action="store_true")

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
        elif args.command == "dump-strings":
            result = inspect_string_pool(args.file, limit=args.limit)
        elif args.command == "dump-literals":
            result = inspect_string_literals(args.file, limit=args.limit)
        elif args.command == "dump-images":
            result = inspect_images(args.file, limit=args.limit)
        elif args.command == "dump-assemblies":
            result = inspect_assemblies(args.file, limit=args.limit)
        elif args.command in ("dump-types", "dump-fields", "dump-methods", "dump-parameters"):
            result = inspect_table(args.file, args.command.removeprefix("dump-"), limit=args.limit)
        elif args.command == "inspect-model":
            result = inspect_model(args.file)
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
    except (AnalyzerError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
