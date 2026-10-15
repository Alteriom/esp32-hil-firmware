# 02_publish — a person tags, the release is checked

One job: after a person pushes the tag, check that `Release` built and attached exactly what a rig will pin.

## Inputs
- Working (this run): `.github/icm/02-release/stages/01_plan/output/plan.md`
- Reference (every run): `.github/icm/_shared/release.md`

Do NOT load: the other pipelines, other runs' output.

## Process
1. The person pushes the tag with the commands in `plan.md`. The agent never runs `git tag`, pushes a tag, runs `gh release create` or dispatches `release.yml`.
2. Watch the tag's `Release` run (`gh run list --workflow release.yml --limit 3`, then `gh run watch <id>`). A red "The tag is the version" step means the number was wrong: say so; the person decides the new tag.
3. Check the release (`gh release view v<version> --repo Alteriom/esp32-hil-firmware`): `alteriom-hil-canary-<version>.tar.gz`, `firmware.json`, `SHA256SUMS`; download `firmware.json` and confirm its `version`, `families`, `commands` and `pins`.

## Outputs
- publish.md → output/ — the tag, the release run and its result, each asset, the downloaded `firmware.json`'s key fields.

## Human check
A person pushes the tag, then reads `publish.md` and confirms the release page shows the three assets.
