# GitHub Release Python distributions

The narrow GA distribution channel is GitHub Releases. Endeavor does **not**
publish to PyPI or another package index for this release line.

For every release tag, the release workflow creates and attaches these
independently checksummed, GitHub-attested assets:

- `endeavor_oscal-<PEP440-VERSION>-py3-none-any.whl`: the preferred universal
  Python wheel;
- `endeavor_oscal-<PEP440-VERSION>.tar.gz`: the standard PEP 517 source
  distribution (sdist);
- `EndeavorOSCAL-<SEMVER-VERSION>-source.tar.gz`: a Git source archive for
  source review and provenance, distinct from the installable sdist;
- `sbom.cdx.json`, `release-manifest.json`, and `SHA256SUMS`.

The release workflow builds the wheel and sdist twice from the exact tagged Git
archive with `SOURCE_DATE_EPOCH` set to the frozen commit timestamp. It rejects
any byte difference, then installs each artifact in a new virtual environment
outside the checkout and runs the installed `endeavor` console command.

## Install

Download the exact wheel from the GitHub Release after verifying it as described
in [the GA draft-release verification runbook](ga-draft-release-verification.md).
From the directory that contains the download:

```sh
python3 -m pip install ./endeavor_oscal-<PEP440-VERSION>-py3-none-any.whl
endeavor --help
```

If a wheel is unsuitable for the target environment, install the matching sdist
instead. Building an sdist requires a compatible local Python build environment
and may download its pinned runtime dependency:

```sh
python3 -m pip install ./endeavor_oscal-<PEP440-VERSION>.tar.gz
endeavor --help
```

Upgrade or remove the distribution using normal pip operations:

```sh
python3 -m pip install --upgrade ./endeavor_oscal-<PEP440-VERSION>-py3-none-any.whl
python3 -m pip uninstall endeavor-oscal
```

The project supports Python versions declared in `pyproject.toml`; the narrow
GA support boundary and supported evidence inputs remain in `SUPPORT.md` and
the compatibility matrix. Installation does not install, configure, or replace
OpenSCAP.
