# OpenSCAP XCCDF tailoring input provenance

These files are immutable upstream OpenSCAP 1.4.4 test inputs. They are not
assessment results and must not be presented as such.

| File | Source | SHA-256 |
| --- | --- | --- |
| `openscap-1.4.4-baseline.xccdf.xml` | `https://github.com/OpenSCAP/openscap/blob/1.4.4/tests/API/XCCDF/tailoring/baseline.xccdf.xml` | `401a2403a88a12922d833d95bc4e0b69b71da5757bf8e8269df9c95e0520c4e0` |
| `openscap-1.4.4-baseline.tailoring.xml` | `https://github.com/OpenSCAP/openscap/blob/1.4.4/tests/API/XCCDF/tailoring/baseline.tailoring.xml` | `74f23255019049cad1e87bad47a367d418bf484febdf11489ee3e91421fb7a2a` |

Both originate from OpenSCAP commit
`4ac56ce0e6dfdea7215b5ad202b3db20855d2507` (tag `1.4.4`) and were retrieved
on 2026-08-30 without transformation. The upstream test
`tests/API/XCCDF/tailoring/all.sh` runs `oscap xccdf eval --tailoring-file ...
--results-arf ...` and asserts an embedded Tailoring/Profile, but removes its
temporary generated output. A future output derived here must record evaluator
NEVRA/image, exact command, input and output hashes, and any sanitization.

## Generated-sanitized ARF result

`fixtures/arf/openscap-1.4.4-tailoring-sanitized.arf.xml` was generated on
2026-08-30 with Fedora 43 image
`registry.fedoraproject.org/fedora:43@sha256:26a6fa6061ce1cf1e1592079e072c0dac77c0cdc50e8e306690febca1165b674`
and `openscap-scanner-1.4.4-1.fc43` using:

`oscap xccdf eval --tailoring-file /work/openscap-1.4.4-baseline.tailoring.xml --results-arf /output/openscap-1.4.4-tailoring-generated.arf.xml /work/openscap-1.4.4-baseline.xccdf.xml`

The complete referenced `baseline.oval.xml` input has SHA-256
`177fe196551e72d4d0c9509f45a59bb4479c2606dd79731bf4cd4b27b4500baf`.
The raw generated ARF had SHA-256
`336b1728e2ff2f7129c98547dc3a59ccaf959b8c33971b383945d52890918560` and is
not committed. `scripts/sanitize-openscap-arf.py` replaced only the disposable
container hostname, bridge IPv4 address, and non-loopback MAC address. The
sanitized ARF SHA-256 is
`05d00bf7cc83d32dc04ebe0bdb9b9404780878b6992dc2e2d5d57d6f2c865543`.

To reproduce, run `scripts/generate-openscap-tailoring-arf.sh` only with
temporarily authorized Docker access. It writes the sanitized artifact, removes
the raw evaluator output on success, and prints the resulting hash. Disable the
workflow by simply not invoking the script; it is not a service or CI job.
