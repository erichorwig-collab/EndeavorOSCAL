#!/usr/bin/env python3
"""Run a finite, deterministic mutation corpus against Endeavor XML parsers."""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
import random
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from endeavor.arf import inspect_arf
from endeavor.oval import OvalInputError, parse_results
from endeavor.xccdf import inspect_xccdf


DEFAULT_CASES = 24
MIN_CASES = 18
MAX_CASES = 96


def _stable(value: object) -> object:
    if is_dataclass(value):
        return _stable(asdict(value))
    if isinstance(value, dict):
        return {key: _stable(item) for key, item in value.items() if key not in {"path", "sha256"}}
    if isinstance(value, (list, tuple)):
        return [_stable(item) for item in value]
    return value


def _canonical(value: object) -> str:
    return json.dumps(_stable(value), sort_keys=True, separators=(",", ":"))


def _root_start(data: bytes) -> int:
    declaration_end = data.find(b"?>")
    return data.find(b"<", declaration_end + 2 if declaration_end >= 0 else 0)


def _forbidden_doctype(data: bytes, _: random.Random) -> bytes:
    start = _root_start(data)
    return data[:start] + b"<!DOCTYPE endeavor-fuzz [<!ENTITY probe 'blocked'>]>" + data[start:]


def _truncated(data: bytes, rng: random.Random) -> bytes:
    return data[:rng.randrange(1, len(data))]


def _nul_byte(data: bytes, rng: random.Random) -> bytes:
    position = rng.randrange(1, len(data))
    return data[:position] + b"\x00" + data[position + 1 :]


def _wrong_root(data: bytes, _: random.Random, root_token: bytes) -> bytes:
    return data.replace(root_token, b"<endeavor-fuzz-root", 1)


def _schema_hint(data: bytes, _: random.Random) -> bytes:
    start = _root_start(data)
    end = data.find(b">", start)
    if start < 0 or end < 0:
        raise ValueError("source fixture has no root start tag")
    opening = data[start : end + 1]
    hint = b' xsi:schemaLocation="https://example.invalid/endeavor-fuzz.xsd"'
    if b"xmlns:xsi=" not in opening:
        hint = b' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' + hint
    return data[:end] + hint + data[end:]


SOURCES = (
    {
        "name": "oval-results",
        "path": ROOT / "fixtures" / "oval-results" / "pass.xml",
        "parse": parse_results,
        "suffix": ".xml",
        "root-token": b"<oval_results",
    },
    {
        "name": "xccdf-results",
        "path": ROOT / "fixtures" / "xccdf-results" / "openscap-1.4.4-results-xccdf12.xml",
        "parse": inspect_xccdf,
        "suffix": ".xml",
        "root-token": b"<Benchmark",
    },
    {
        "name": "arf-collection",
        "path": ROOT / "fixtures" / "arf" / "openscap-1.4.4-xccdf-overrides.arf.xml",
        "parse": inspect_arf,
        "suffix": ".xml",
        "root-token": b"<arf:asset-report-collection",
    },
)
REJECTING_MUTATIONS = ("forbidden-doctype", "truncated", "nul-byte", "wrong-root")


def _mutate(name: str, data: bytes, rng: random.Random, root_token: bytes) -> bytes:
    if name == "forbidden-doctype":
        return _forbidden_doctype(data, rng)
    if name == "truncated":
        return _truncated(data, rng)
    if name == "nul-byte":
        return _nul_byte(data, rng)
    if name == "wrong-root":
        return _wrong_root(data, rng, root_token)
    if name == "schema-hint":
        return _schema_hint(data, rng)
    raise ValueError(f"unknown mutation: {name}")


def _cases(count: int, rng: random.Random) -> list[tuple[dict[str, object], str]]:
    required = [(source, mutation) for source in SOURCES for mutation in REJECTING_MUTATIONS]
    required.extend((source, "schema-hint") for source in SOURCES)
    selected = list(required)
    candidates = [(source, mutation) for source in SOURCES for mutation in (*REJECTING_MUTATIONS, "schema-hint")]
    while len(selected) < count:
        selected.append(rng.choice(candidates))
    return selected


def run(cases: int, seed: int) -> dict[str, object]:
    if not MIN_CASES <= cases <= MAX_CASES:
        raise ValueError(f"cases must be between {MIN_CASES} and {MAX_CASES}")
    rng = random.Random(seed)
    baselines = {source["name"]: _canonical(source["parse"](source["path"])) for source in SOURCES}
    outcomes: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="endeavor-fuzz-") as directory:
        workspace = Path(directory)
        for index, (source, mutation) in enumerate(_cases(cases, rng), start=1):
            source_name = str(source["name"])
            payload = _mutate(mutation, source["path"].read_bytes(), rng, source["root-token"])
            path = workspace / f"case-{index:03d}-{source_name}{source['suffix']}"
            path.write_bytes(payload)
            try:
                result = source["parse"](path)
            except OvalInputError as error:
                if mutation == "schema-hint":
                    raise ValueError(f"{source_name}/{mutation} was rejected: {error}") from error
                if str(path.parent) in str(error):
                    raise ValueError(f"{source_name}/{mutation} disclosed a temporary path") from error
                outcomes.append({"source": source_name, "mutation": mutation, "outcome": "rejected"})
                continue
            except Exception as error:
                raise ValueError(f"{source_name}/{mutation} raised an unexpected {type(error).__name__}") from error
            if mutation != "schema-hint":
                raise ValueError(f"{source_name}/{mutation} was accepted")
            if _canonical(result) != baselines[source_name]:
                raise ValueError(f"{source_name}/{mutation} changed the accepted inventory")
            outcomes.append({"source": source_name, "mutation": mutation, "outcome": "accepted-identical"})
    return {
        "format": "endeavor-untrusted-xml-fuzz-regression",
        "version": "1.0.0",
        "status": "passed",
        "seed": seed,
        "cases": outcomes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260831)
    parser.add_argument("--cases", type=int, default=DEFAULT_CASES)
    args = parser.parse_args(argv)
    try:
        payload = run(args.cases, args.seed)
    except (OSError, ValueError) as error:
        print(f"untrusted XML fuzz regression failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
