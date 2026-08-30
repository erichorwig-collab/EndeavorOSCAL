from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from .convert import assessment_results
from .mapping import mapping_report, parse_mapping
from .oval import OvalInputError, parse_definitions, parse_results


class ExitCode:
    """Stable process exit codes for Endeavor's public CLI."""

    SUCCESS = 0
    USAGE = 2
    INPUT = 3
    OUTPUT = 4
    INTERNAL = 5


class UsageError(ValueError):
    """Command-line arguments do not meet the public CLI contract."""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UsageError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="endeavor", description="Convert OVAL evidence to OSCAL Assessment Results.")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_ArgumentParser)
    for name in ("inspect", "convert", "mapping-report"):
        command = sub.add_parser(name)
        command.add_argument("--results", required=True, type=Path)
        command.add_argument("--definitions", required=True, type=Path)
        command.add_argument("--format", choices=("text", "json"), default="text", help="format handled diagnostics as text or JSON")
        if name == "convert":
            command.add_argument("--output", required=True, type=Path)
            command.add_argument("--mapping", type=Path, help="explicit versioned OVAL-to-OSCAL mapping")
        if name == "mapping-report":
            command.add_argument("--mapping", required=True, type=Path)
    return parser


def _error_payload(code: str, message: str, exit_code: int) -> str:
    return json.dumps(
        {"error": {"code": code, "exit-code": exit_code, "message": message}},
        separators=(",", ":"),
        sort_keys=True,
    )


def _report_error(args: argparse.Namespace | None, code: str, message: str, exit_code: int) -> int:
    if args is not None and args.format == "json":
        print(_error_payload(code, message, exit_code), file=sys.stderr)
    else:
        print(f"endeavor: {code}: {message}", file=sys.stderr)
    return exit_code


def main(argv: list[str] | None = None) -> int:
    args: argparse.Namespace | None = None
    try:
        args = _parser().parse_args(argv)
        results = parse_results(args.results)
        definitions = parse_definitions(args.definitions)
        if args.command == "inspect":
            payload = {"results": {"path": results.path.name, "sha256": results.sha256, "generator": results.generator.__dict__, "definition-results": [{"id": item.identifier, "result": item.result} for item in results.definitions]}, "definitions": {"path": definitions.path.name, "sha256": definitions.sha256, "generator": definitions.generator.__dict__, "definition-count": len(definitions.definitions)}}
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif args.command == "mapping-report":
            print(json.dumps(mapping_report(results, definitions, parse_mapping(args.mapping)), indent=2, sort_keys=True))
        else:
            payload = assessment_results(results, definitions, parse_mapping(args.mapping) if args.mapping else None)
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
    except UsageError as exc:
        return _report_error(args, "usage", str(exc), ExitCode.USAGE)
    except OvalInputError as exc:
        return _report_error(args, "input-invalid", str(exc), ExitCode.INPUT)
    except OSError as exc:
        return _report_error(args, "output-failed", "could not write output artifact", ExitCode.OUTPUT)
    return ExitCode.SUCCESS
