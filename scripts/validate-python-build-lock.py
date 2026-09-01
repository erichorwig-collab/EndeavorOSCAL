#!/usr/bin/env python3
"""Fail closed when the CI-only Python build lock drifts or loses a hash."""

from __future__ import annotations

from pathlib import Path
import re
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "requirements-python-build.lock"
EXPECTED = {
    "lxml": "6.1.2",
    "build": "1.3.0",
    "packaging": "26.3",
    "pyproject-hooks": "1.2.0",
    "setuptools": "83.0.0",
}
LINE = re.compile(r"([A-Za-z0-9_.-]+)==([0-9][A-Za-z0-9_.!+-]*)\s+--hash=sha256:([0-9a-f]{64})$")


def main() -> int:
    try:
        entries: dict[str, tuple[str, str]] = {}
        for raw in LOCK.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            match = LINE.fullmatch(line)
            if match is None:
                raise ValueError("lock contains an unsupported or unhashed requirement")
            name, version, digest = match.groups()
            name = name.lower().replace("_", "-")
            if name in entries:
                raise ValueError("lock contains a duplicate requirement")
            entries[name] = (version, digest)
        if {name: version for name, (version, _) in entries.items()} != EXPECTED:
            raise ValueError("lock does not match the declared CI build toolchain")
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        if f"lxml=={entries['lxml'][0]}" not in pyproject["project"]["dependencies"]:
            raise ValueError("lock lxml version does not match pyproject.toml")
        if pyproject["build-system"]["requires"] != [f"setuptools=={entries['setuptools'][0]}"]:
            raise ValueError("lock setuptools version does not match pyproject.toml")
    except (OSError, ValueError, KeyError, tomllib.TOMLDecodeError) as error:
        print(f"Python build lock validation failed: {error}", file=sys.stderr)
        return 1
    print("Python build lock is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
