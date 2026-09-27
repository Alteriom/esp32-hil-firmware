# AGENTS.md — esp32-hil-firmware

Instructions for AI coding agents (Claude Code, Copilot, Codex, Cursor). Humans: start with README.md.

## What this repo is

The **Rig Health Check** firmware (historically "canary"): one image per family (esp32, esp32-c3,
esp32-c5, esp32-c6, esp32-s3, esp8266) that a rig flashes to prove its own hardware. It is released
here and **pinned** by the rig (`canary/firmware.json` in `Alteriom/esp32-rig`); the rig compiles
nothing. Public, Apache-2.0.

One of four repositories that must stay consistent:

| Repo | Role |
|---|---|
| `Alteriom/esp32-rig` (public) | The rig software; pins a release of this repo and holds the health check *suite* (`suites/canary`) |
| `Alteriom/esp32-hil-firmware` (this) | The firmware and its release bundle |
| `Alteriom/esp32-rig-example` (public) | Example project every rig ships |
| The Alteriom farm portal (a private repository) | Consumes rig releases |

## Where to look

| Question | File |
|---|---|
| The serial protocol and the checks the firmware answers | `firmware/src/main.cpp`, `firmware/src/canary_platform.h` |
| Families, boards, PlatformIO envs | `firmware/platformio.ini` |
| Version (MAJOR.MINOR, moved by hand) | `firmware/VERSION` |
| How the bundle and `firmware.json` are built and versioned | `build_artifacts.py` (`--version` prints what the tree builds) |
| What CI checks | `tests/test_build.py`, `tests/test_firmware.py`, `.github/workflows/build.yml` |
| Release | `.github/workflows/release.yml` (tag `vMAJOR.MINOR.PATCH`) |

## Commands

```bash
python -m pip install pytest && python -m pytest -q          # fast checks, no toolchain
python -m pip install platformio esptool
python build_artifacts.py --out hil-canary                   # every family
python build_artifacts.py --out hil-canary --target esp32-c6 # one family
python build_artifacts.py --version                          # the version a tag must carry
```

Each family builds in its own PlatformIO core under `~/.platformio-cores/` (`ALTERIOM_PIO_CORES`):
the two Arduino cores ship a package of the same name and cannot share one.

## Rules

- **Versions are computed, not chosen.** PATCH = number of commits that changed `firmware/`; the
  release refuses a tag that disagrees with `build_artifacts.py --version`.
- **The protocol is shared with the rig's suite** (`suites/canary` in `esp32-rig`) and with the rig's
  simulator. `firmware.json` carries `commands` and per-family `pins`; the rig holds its client,
  simulator and wiring table to those. A new or changed command needs the matching change in the rig.
- **Three identities** travel in the manifest: `farm_sha` (last commit that changed `firmware/`),
  `canary_sha` (digest of `firmware/`, reported by a board over serial), `version` (compiled in).
  Don't break any of them.
- **Changing what rigs run** = release here, then move the pin in `esp32-rig` (one reviewed line),
  then a rig release. Nothing reaches a rig until that pin moves.
- Public repo: no internal hostnames, IPs, tokens or private repo names.

## Conventions

Small PRs, squash-merged; CI builds every family and verifies the bundle the way a rig does.
