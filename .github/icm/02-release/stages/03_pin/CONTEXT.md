# 03_pin — the rig's pin, prepared for a person

One job: the one-line pin change for `Alteriom/esp32-rig`, and anything else the rig must change with it, ready for a person to open there.

## Inputs
- Working (this run): `.github/icm/02-release/stages/02_publish/output/publish.md`
- Reference (every run): `.github/icm/_shared/release.md`
- Reference (only when the release changed `commands`, `pins` or the families): `.github/icm/_shared/rules.md`

Do NOT load: the other pipelines, other runs' output.

## Process
1. The pin is the release's `firmware.json`, verbatim, as `canary/firmware.json` in `Alteriom/esp32-rig` ([release.md](../../../_shared/release.md) "Delivery: the rig's pin"). Prepare its content and a pull request title and body that name this release and what changed for a rig.
2. If `commands`, `pins` or the families changed, list what the rig's suite (`suites/canary`), simulator and wiring table must change in the same pull request or before it ([rules.md](../../../_shared/rules.md) "The protocol is shared").
3. Nothing here edits the rig: a person opens the pull request there, or an agent working in that repository takes it through its own `firmware` route.

## Outputs
- pin.md → output/ — the new `canary/firmware.json` content, the pull request title and body for the rig, and what else the rig must change.

## Human check
A person opens (or asks for) the rig's pin pull request from `pin.md`; rigs run the new firmware only after it merges and the rig releases.
