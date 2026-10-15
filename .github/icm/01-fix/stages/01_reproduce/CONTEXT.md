# 01_reproduce — reproduce the reported defect

One job: turn the report into something that fails on demand, for the reason reported.

## Inputs
- Working (this run): the report — read whole with what it links: an issue (`gh issue view <n> --comments`), a red run (`gh run view <run-id> --log-failed`), a rig's health check report and serial capture, or the agreed request from route `protocol`.
- Reference (every run): `.github/icm/_shared/architecture.md`
- Reference (every run): `.github/icm/_shared/rules.md`
- Reference (only when the defect is in the build, the numbering or a workflow): `.github/icm/_shared/build-and-test.md`

Do NOT load: the other pipelines, other runs' output, `.github/icm/_shared/release.md`.

## Process
1. Restate the report as observed versus expected: which family, which command or check, what the board said (the serial line), which release of this firmware the rig had pinned.
2. Decide whose it is. A red check on one board of a family, with the others green, is usually the board or its wiring, not the firmware; a red check on every board of a family, or a wrong answer to a command, is the firmware's. The rig's suite is in `Alteriom/esp32-rig` (`suites/canary`): if the suite is wrong, the fix is there, and this run stops with the reproduction for that repository.
3. Find the code with [architecture.md](../../../_shared/architecture.md) and name the suspected cause as `path:line`.
4. Write a fast check in `tests/` that fails for that cause, the way the existing ones do (they read the source and the build, no toolchain); a compile error is reproduced by building that family.
5. Run it and keep the failing output.

## Outputs
- reproduction.md → output/ — the restated report; whose it is and why; suspected cause (`path:line`); the check or build command; the failing output; what only a rig can show.

## Human check
A person runs the command, or reads the evidence, and confirms it fails for the reported reason and that the cause is in this repository.
