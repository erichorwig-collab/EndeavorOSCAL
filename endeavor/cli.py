from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from .convert import assessment_results
from .oval import OvalInputError, parse_definitions, parse_results


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="endeavor", description="Convert OVAL evidence to OSCAL Assessment Results.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "convert"):
        command = sub.add_parser(name)
        command.add_argument("--results", required=True, type=Path)
        command.add_argument("--definitions", required=True, type=Path)
        if name == "convert":
            command.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        results = parse_results(args.results)
        definitions = parse_definitions(args.definitions)
        if args.command == "inspect":
            payload = {"results": {"path": str(results.path), "sha256": results.sha256, "generator": results.generator.__dict__, "definition-results": [{"id": item.identifier, "result": item.result} for item in results.definitions]}, "definitions": {"path": str(definitions.path), "sha256": definitions.sha256, "generator": definitions.generator.__dict__, "definition-count": len(definitions.definitions)}}
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            payload = assessment_results(results, definitions)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(prefix=".endeavor-", suffix=".tmp", dir=args.output.parent)
            temporary_path = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    os.fchmod(stream.fileno(), 0o600)
                    stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
                os.replace(temporary_path, args.output)
            except Exception:
                temporary_path.unlink(missing_ok=True)
                raise
    except OvalInputError as exc:
        print(f"endeavor: error: {exc}", file=sys.stderr)
        return 2
    return 0
