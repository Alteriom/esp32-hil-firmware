# 02-release — the pipeline

The tag is the version, and the rig's pin is the delivery: plan it, let a person tag it, check it, hand over the pin.

| Stage | Job | Input | Output | Human check |
|---|---|---|---|---|
| [`01_plan`](stages/01_plan/CONTEXT.md) | what changed, and the number | the changes since the last release | `output/plan.md` | A person approves the version and the commit; nothing is tagged until they do. |
| [`02_publish`](stages/02_publish/CONTEXT.md) | a person tags, the release is checked | 01_plan's `plan.md` | `output/publish.md` | A person pushes the tag, then reads `publish.md` and confirms the release page shows the three assets. |
| [`03_pin`](stages/03_pin/CONTEXT.md) | the rig's pin, prepared for a person | 02_publish's `publish.md` | `output/pin.md` | A person opens (or asks for) the rig's pin pull request from `pin.md`; rigs run the new firmware only after it merges and the rig releases. |
