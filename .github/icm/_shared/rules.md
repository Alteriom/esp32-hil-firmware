---
verified_at: 2026-10-15
verified_commit: 3b25ad9f17f1bd1af0bf2d028804ccf8d69c56d1
---

# Rules that are easy to break, and the conventions

Each rule names the file or test that holds it.

## The protocol is shared

The serial commands and the per-family pins are shared with the rig's suite (`suites/canary` in `Alteriom/esp32-rig`) and the rig's simulator. `firmware.json` carries `commands` and `pins`, read from the source by `commands` and `pins` in `build_artifacts.py`, so that a rig holds its client, simulator and wiring table to the firmware it pins (`README.md` "What a release is"). A new or changed command, check, family or pin table needs the matching change in the rig, agreed before the code and released after this one. `tests/test_firmware.py` `test_the_commands_are_the_dispatch_chain` and `tests/test_build.py` `test_the_pin_tables_travel_with_the_release` hold the two lists to the source; `test_the_targets_are_the_families_a_rig_supports` holds the families.

## The three identities

`farm_sha` (the last commit that changed `firmware/`), `canary_sha` (the digest of `firmware/`, which a board reports over serial) and `version` (compiled in) travel in the manifest; don't break any of them (`build_artifacts.py` docstring, `README.md` "What a release is", `tests/test_build.py`). Versions are computed, not chosen: PATCH is the number of commits that changed `firmware/`, and the release refuses a tag that disagrees with `build_artifacts.py --version` ([release.md](release.md)).

## The source's bytes are its identity

`.gitattributes` forces LF everywhere: `canary_sha` is the digest of the source byte for byte, so a checkout that turned the source into CRLF would build a different firmware. Never commit a file under `firmware/` with other line endings.

## What the firmware may depend on

Nothing a consumer ships: the includes and the one library (`bblanchon/ArduinoJson`) are listed in `tests/test_firmware.py` `test_the_firmware_carries_no_consumer_code`, which is what makes a red health check never somebody's regression. Each other test there is a bug a rig found (a truncated line, a timeout in the wrong units, a read that gave up early); keep them.

## Conventions

- Small pull requests, squash-merged; `build.yml` builds every family and verifies the bundle the way a rig does.
- Changing what rigs run is three steps, in order: a release here, the pin moved in `Alteriom/esp32-rig` (one reviewed line), then a rig release. Nothing reaches a rig until that pin moves ([release.md](release.md)).
- Public repository: no internal host name, address, token or private repository name in code, comments, workflows or these files (`README.md` names only the public repositories).
