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
