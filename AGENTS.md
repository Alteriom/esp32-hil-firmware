# AGENTS.md — esp32-hil-firmware

The **Rig Health Check** firmware (historically "canary"): one image per family (esp32, esp32-c3, esp32-c5, esp32-c6, esp32-s3, esp8266) that an ESP32 HIL rig flashes to prove its own hardware. It is released here by tag and **pinned** by the rig, `Alteriom/esp32-rig` (`canary/firmware.json` there); the rig compiles nothing. Public, Apache-2.0. Humans: start with `README.md`. For Claude Code, Copilot, Codex and Cursor alike (`CLAUDE.md` and `.github/copilot-instructions.md` point here). Keep this file short and true; update it in the pull request that makes it wrong.

## Where things live

| Path | What it holds |
|---|---|
| `firmware/` | the source (`src/main.cpp`, `src/canary_platform.h`), one PlatformIO env per family (`platformio.ini`), `VERSION` (MAJOR.MINOR, moved by hand) |
| `build_artifacts.py` | builds the bundle and `firmware.json`, and says what the tree is (`--version`, `--revision`) |
| `tests/` | the fast checks, no toolchain: numbering and identity (`test_build.py`), what the source promises (`test_firmware.py`) |
| `.github/workflows/` | `build.yml` (tests, every family built and verified like a rig), `release.yml` (`v*` tags), `icm-check.yml` |
| [`.github/icm/_shared/`](.github/icm/_shared/CONTEXT.md) | what every job below draws on, one file per question |
| [`.github/icm/01-fix/`](.github/icm/01-fix/CLAUDE.md) | fix a defect in the firmware, the build or a check |
| [`.github/icm/02-release/`](.github/icm/02-release/CLAUDE.md) | release a version (a person tags it) and prepare the rig's pin |

## Route by what just happened

| Route | If | Go to | Then stop at |
|---|---|---|---|
| triage | an issue or report arrives and its kind is unclear | read it whole, then take the row below that fits | the row chosen, said to the person |
| fix | a defect is reported: a red health check that is the firmware's own bug, a family that does not build, a wrong manifest | [01_reproduce](.github/icm/01-fix/stages/01_reproduce/CONTEXT.md) | a person has seen the reproduction fail |
| ci-red | `Build` or `Release` is red on `main` or on a tag | [01_reproduce](.github/icm/01-fix/stages/01_reproduce/CONTEXT.md), with the run log as the report | a person has seen the reproduction fail |
| protocol | a serial command, a check, a family or a pin table is to be added or changed | [rules.md](.github/icm/_shared/rules.md) "The protocol is shared", then route `fix` with the request as the report | a person agrees the matching `Alteriom/esp32-rig` change before any code |
| release | a version is to be released, or rigs should run a newer firmware | [01_plan](.github/icm/02-release/stages/01_plan/CONTEXT.md) | a person approves the version |
| next | a stage's output was approved | the next numbered stage of the same job | a person reads that stage's output |
| status | asked for status | scan `.github/icm/*/stages/*/output/` | report what exists |

## Agents connecting remotely

This repository becomes the ICM workspace `esp32-hil-firmware` on MemoryRelay, created by a person from this repository's `main`; the Alteriom hub `portfolio` then delegates to it. Until the workspace exists, an agent on a clone reads these files directly: this file is the entry and the table above is the route. Once it exists, an agent that is not on a clone reaches the same files over MCP at `https://api.memoryrelay.net/mcp` with a key in `MEMORYRELAY_API_KEY`; none of it holds a secret.

- Start with `icm_context_build` for the route that fits (`{kind: "route", id: "fix"}`), not with the whole repository.
- Report what you read with `icm_report_reads` when a stage ends, and what the task came to with `icm_report_outcome`.
- Never write through MCP: a change is a branch and a pull request here, read and merged by a person.

## Rules

- Nothing moves to the next stage until a person has read the output of the last one.
- A stage writes to its own `output/`, which is not committed: one run per worktree or branch; clear that job's `stages/*/output/` when its pull request merges or is abandoned.
- `.github/icm/` points at the files that own each fact. When they disagree, the owning file is right: correct `.github/icm/` in the same pull request and bump its `verified_commit`.
- No stage pushes a tag, publishes a release or edits `Alteriom/esp32-rig`: a person does ([release.md](.github/icm/_shared/release.md)).
- Public repository: no internal host name, address, token or private repository name, in code or in these files ([rules.md](.github/icm/_shared/rules.md)).
