---
verified_at: 2026-10-15
verified_commit: 3b25ad9f17f1bd1af0bf2d028804ccf8d69c56d1
---

# Architecture — where to look

A map for finding the file that owns a fact. What the firmware checks and why it lives on its own: `README.md` and the docstring of `build_artifacts.py`.

## Four repositories, kept consistent

| Repository | Role |
|---|---|
| `Alteriom/esp32-hil-firmware` (this) | the firmware and its release bundle |
| `Alteriom/esp32-rig` | the rig software: pins a release of this repository in its `canary/firmware.json`, carries the bundle in its own release, and holds the health check *suite* (`suites/canary`) that drives this firmware over serial |
| `Alteriom/esp32-rig-example` | the example project every rig ships; it does not use this firmware |
| the farm portal (a private repository) | consumes rig releases and follows the rig's pin |

## Where to look

| Question | Where |
|---|---|
| the serial protocol and the checks the firmware answers | `firmware/src/main.cpp` (the dispatch chain), `firmware/src/canary_platform.h` (what differs per core) |
| families, boards, PlatformIO environments, the one library allowed | `firmware/platformio.ini` |
| the families, chips and bootloader offsets the build knows | `TARGETS` in `build_artifacts.py` |
| the version's MAJOR.MINOR | `firmware/VERSION` |
| how the bundle, its manifest (schema 2) and `firmware.json` are built | `build_artifacts.py` (`build_artifacts`, `describe`; `commands` and `pins` read the source for `firmware.json`) |
| what a rig pins, per field | `README.md` "What a release is" |
| the checks without a toolchain | `tests/test_build.py`, `tests/test_firmware.py` |
| CI and the release | `.github/workflows/build.yml`, `.github/workflows/release.yml` |
