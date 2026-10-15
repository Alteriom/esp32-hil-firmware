---
verified_at: 2026-10-15
verified_commit: 3b25ad9f17f1bd1af0bf2d028804ccf8d69c56d1
---

# Build, test, and what counts as evidence

What CI runs is `.github/workflows/build.yml`; read its steps rather than copying them anywhere. The person's version is `README.md` "Building it yourself".

## The fast checks, and a build

```bash
python -m pip install pytest && python -m pytest -q          # fast checks, no toolchain
python -m pip install platformio esptool
python build_artifacts.py --out hil-canary                   # every family
python build_artifacts.py --out hil-canary --target esp32-c6 # one family
python build_artifacts.py --version                          # the version a tag must carry
python build_artifacts.py --revision                         # the source digest a board reports
```

Each family builds in its own PlatformIO core under `~/.platformio-cores/` (`ALTERIOM_PIO_CORES` moves it; `core_dir_for` in `build_artifacts.py`): the two Arduino cores ship a package of the same name and cannot share one. A full build installs six toolchains; CI frees disk space first.

The version and the identities are read from git history (`firmware_version`, `farm_sha` in `build_artifacts.py`): a shallow clone fails the build rather than stamping a wrong number, so CI checks out with `fetch-depth: 0` and `tests/test_build.py` needs a full clone. A modified or untracked file under `firmware/` marks the version `+modified`: that build is not the version it would claim.

## What CI runs, and when

| Workflow | Runs | On |
|---|---|---|
| `build.yml` `tests` | `python -m pytest -q` | every pull request and push to `main` |
| `build.yml` `firmware` | every family built, then the bundle verified the way a rig does (schema 2, each image's digest, every component at its offset), uploaded as `hil-canary` | every pull request and push to `main` |
| `release.yml` | the release ([release.md](release.md)) | `v*` tags; a dispatch against a ref builds and attaches nothing |
| `icm-check.yml` | the workspace files compile to the ICM standard | changes to the entry files or `.github/icm/`; weekly with `--strict` |

## Evidence

- A fast check that fails without the change, in `tests/` (each test there came from a rig: the docstring of `tests/test_firmware.py`).
- A source change is proven compiled by `build.yml` `firmware` for every family, not by one local family.
- What the firmware does on a board is proven only on a rig: the health check suite in `Alteriom/esp32-rig` (`suites/canary`) flashes the bundle and drives it. Say in the pull request which rig run, or that none was made.
