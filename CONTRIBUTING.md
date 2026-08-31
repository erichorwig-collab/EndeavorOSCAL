# Contributing to Endeavor

## Before opening a change

- File an issue first for new source-format support, mapping semantics, or
  behavior that changes the published support boundary.
- Keep real assessment evidence out of the repository. Fixtures must be
  sanitized, source-provenance documented, and safe to publish.
- Preserve Endeavor's core rule: source status and provenance are retained;
  OSCAL output must never be presented as re-executable OVAL logic.

## Pull requests

1. Make each change focused and update the affected contract, compatibility
   matrix, or release note.
2. Add regression coverage for changed parsing, mapping, CLI, or security
   behavior.
3. Run `python3 -m unittest discover -s tests -v` and the applicable release
   readiness validator.
4. State fixture provenance, any compatibility impact, and any remaining
   validation limitation in the pull request description.

Maintainers may request an independently reproducible source artifact for
release-affecting changes. Contributions are licensed under the repository's
Apache-2.0 license.
