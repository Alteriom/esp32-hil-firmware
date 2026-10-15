# 02-release — release a version and prepare the rig's pin

One run is one release: the number the tree builds, the tag pushed by a person and the release checked, then the one-line pin change prepared for `Alteriom/esp32-rig`. No stage pushes a tag, publishes a release or edits the rig: a person does, from what the stage prepared.

Stages, in order; inputs, outputs and checks for each are in [CONTEXT.md](CONTEXT.md):

1. [Plan](stages/01_plan/CONTEXT.md) — what changed in `firmware/`, and the number.
2. [Publish](stages/02_publish/CONTEXT.md) — a person tags; the release and its assets are checked.
3. [Pin](stages/03_pin/CONTEXT.md) — the rig's pin change, prepared for a person.
