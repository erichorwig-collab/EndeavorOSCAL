# Generated-sanitized OpenSCAP fixture provenance

This is a project-authored, generated-sanitized fixture. It is genuine
OpenSCAP evaluator output, but is not an upstream scan artifact and must not
be represented as one.

| Field | Value |
| --- | --- |
| Definition author | Endeavor project |
| Evaluator | OpenSCAP 1.4.4 (`openscap-scanner-1:1.4.4-1.fc43`) |
| Evaluator image | `registry.fedoraproject.org/fedora:43@sha256:26a6fa6061ce1cf1e1592079e072c0dac77c0cdc50e8e306690febca1165b674` |
| Declared OVAL core version | 5.11.3 |
| Evaluation command | `oscap oval eval --results /work/oval-results.xml /work/oval-definitions.xml` |
| Evaluation outcome | `oval:org.endeavor.fixture:def:1: true` |
| Source Definition SHA-256 | `0b1bee7b1c89d6f43fbbde3604d51b21b4069e5e3da1be0893177032cdae28c8` |
| Raw Results SHA-256 (not retained) | `1a31fed12ba6602f3f6151028985941a371242febc989675a3e9503f16da5846` |
| Sanitized Results SHA-256 | `90c8df16b9c6329d94db229dd7321d2892db4a94154bd1b83d0f92350e30c2f4` |

The disposable Fedora container was permitted network access only to install
the evaluator packages. The `family_test` itself does not use network input.

## Sanitization log

The source definition intentionally collects only the OS family. The generated
Results artifact was transformed with
`scripts/sanitize-openscap-results.py` before it was committed:

1. Replaced the disposable container hostname with `endeavor-oval-fixture`.
2. Replaced all reported interfaces with one documented loopback interface
   (`127.0.0.1`, `00:00:00:00:00:00`).

No OVAL definition, evaluation outcome, object identifier, system-data family
value, evaluator identity, or evaluator timestamp was changed. The resulting
pair is validated by OpenSCAP during generation and by Endeavor's XML, OSCAL,
and AJV test gates.
