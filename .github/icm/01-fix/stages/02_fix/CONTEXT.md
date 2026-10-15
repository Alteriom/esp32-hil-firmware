# 02_fix — change the cause, not the symptom

One job: the smallest change at the cause that turns the reproduction green, keeping the protocol, the identities and the dependencies as they are unless the run is an agreed protocol change.

## Inputs
- Working (this run): `.github/icm/01-fix/stages/01_reproduce/output/reproduction.md`
- Reference (every run): `.github/icm/_shared/rules.md`
- Reference (every run): `.github/icm/_shared/build-and-test.md`

Do NOT load: the other pipelines, other runs' output, `.github/icm/_shared/release.md`.

## Process
1. Confirm the cause in the code before changing anything.
2. Change it in `firmware/src/` (the two cores differ in `firmware/src/canary_platform.h`), `firmware/platformio.ini` or `build_artifacts.py`. Comment the *why* with what a rig observed.
3. Check [rules.md](../../../_shared/rules.md): no new dependency; `commands`, `pins` and families change only for an agreed protocol change; the three identities still mean what they mean; LF line endings under `firmware/`.
4. Run the reproduction (green now) and `python -m pytest -q`; build the affected families, or all of them ([build-and-test.md](../../../_shared/build-and-test.md)).

## Outputs
- change.md → output/ — the cause in one paragraph; each file changed and why; the passing output; the families built and their result; for a protocol change, the rig change it needs.

## Human check
A person reads the diff beside the reproduction: it removes the cause, adds no dependency, and changes the protocol only if that was agreed.
