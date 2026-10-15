# 01-fix — fix a defect in the firmware, the build or a check

One run is one defect, or one agreed change to a command or check (route `protocol` in the entry): reproduced as a fast check that fails, fixed at its cause, built for every family, and proposed as a pull request. A rig gets it only after a release here and the rig's pin moves (`02-release`).

Stages, in order; inputs, outputs and checks for each are in [CONTEXT.md](CONTEXT.md):

1. [Reproduce](stages/01_reproduce/CONTEXT.md) — make it fail on purpose.
2. [Fix](stages/02_fix/CONTEXT.md) — change the cause, watch the reproduction pass.
3. [Verify](stages/03_verify/CONTEXT.md) — every family built, the pull request.
