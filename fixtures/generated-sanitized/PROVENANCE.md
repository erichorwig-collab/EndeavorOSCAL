# Generated-sanitized OpenSCAP fixture provenance

This is a project-authored, generated-sanitized fixture. It is genuine
OpenSCAP evaluator output, but is not an upstream scan artifact and must not
be represented as one.

| Field | Value |
| --- | --- |
| Definition author | Endeavor project |
| Evaluator | OpenSCAP 1.4.2 (`openscap-scanner-1:1.4.2-2.fc41`) |
| Evaluator image | `registry.fedoraproject.org/fedora:41@sha256:893f7eeffce8e3e2bb2bc62786ba5603fb1e0bd6ba07091acb892266b95bafdf` |
| Declared OVAL core version | 5.11.3 |
| Evaluation command | `oscap oval eval --results /work/oval-results.xml /work/oval-definitions.xml` |
| Evaluation outcome | `oval:org.endeavor.fixture:def:1: true` |
| Source Definition SHA-256 | `0b1bee7b1c89d6f43fbbde3604d51b21b4069e5e3da1be0893177032cdae28c8` |
| Raw Results SHA-256 (not retained) | `b27076899b45efb5c21be4b05fd90c311c6fecfbdf929a302aa21e32d683c3ee` |
| Sanitized Results SHA-256 | `8cf4d88af61fde855369e5fc719f05d2bf2cd9233f5720dc31db4bd346b39840` |

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
