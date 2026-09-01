from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-alpha-review-cache.py"
LAUNCHER = ROOT / "scripts" / "launch-alpha-review-vm.sh"
BOOTSTRAP = ROOT / "scripts" / "prepare-alpha-review-vm.sh"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AlphaReviewCacheTests(unittest.TestCase):
    def make_cache(self, root: Path, candidate: str, requirements: Path, package_lock: Path) -> Path:
        cache = root / "cache"
        (cache / "apk").mkdir(parents=True)
        (cache / "python").mkdir()
        (cache / "npm").mkdir()
        (cache / "apk" / "python3.apk").write_bytes(b"apk")
        (cache / "python" / "lxml-6.1.2-cp314-cp314-musllinux_1_2_x86_64.whl").write_bytes(b"wheel")
        (cache / "npm" / "entry").write_bytes(b"npm")
        (cache / "CACHE-METADATA").write_text(
            "\n".join((
                "format=endeavor-alpha-review-offline-cache",
                "version=1.0.0",
                f"candidate-commit={candidate}",
                f"requirements-sha256={_digest(requirements)}",
                f"package-lock-sha256={_digest(package_lock)}",
                "alpine-version=3.24",
                "",
            )),
            encoding="utf-8",
        )
        files = sorted(path for path in cache.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
        (cache / "SHA256SUMS").write_text("".join(f"{_digest(path)}  {path.relative_to(cache).as_posix()}\n" for path in files), encoding="utf-8")
        return cache

    def validate(self, cache: Path, candidate: str, requirements: Path, package_lock: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(VALIDATOR), "--cache", str(cache), "--candidate", candidate, "--requirements", str(requirements), "--package-lock", str(package_lock)], cwd=ROOT, text=True, capture_output=True, check=False)

    def test_cache_must_be_complete_hash_bound_and_tamper_evident(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            requirements, package_lock = root / "requirements.txt", root / "package-lock.json"
            requirements.write_text("lxml==6.1.2\n", encoding="utf-8")
            package_lock.write_text("{}\n", encoding="utf-8")
            cache = self.make_cache(root, "a" * 40, requirements, package_lock)
            completed = self.validate(cache, "a" * 40, requirements, package_lock)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            (cache / "python" / "lxml-6.1.2-cp314-cp314-musllinux_1_2_x86_64.whl").write_bytes(b"tampered")
            completed = self.validate(cache, "a" * 40, requirements, package_lock)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("checksum", completed.stderr)

    def test_vm_scripts_require_strict_offline_boundary(self) -> None:
        launcher = LAUNCHER.read_text(encoding="utf-8")
        bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn("ENDEAVOR_VM_OFFLINE_CACHE", launcher)
        self.assertIn("readonly=on", launcher)
        self.assertIn("mount_tag=shared", launcher)
        self.assertIn("mount_tag=export", launcher)
        self.assertIn("ENDEAVOR_VM_ALLOW_ONLINE_BOOTSTRAP", launcher)
        self.assertIn("apk add --no-network --no-cache", bootstrap)
        self.assertIn("--no-index --find-links", bootstrap)
        self.assertIn("npm ci --offline --ignore-scripts", bootstrap)

