---
verified_at: 2026-10-15
verified_commit: 3b25ad9f17f1bd1af0bf2d028804ccf8d69c56d1
---

# Documents — what a person reads here, and who owns its facts

The agent-facing files are `AGENTS.md` (the entry) and this folder. The document below restates facts that code or a workflow owns; the owner is right when they disagree. It is pinned in the workspace, so an agent can be given it by path.

| Document | What it answers | Owner of the facts |
|---|---|---|
| [README.md](../../../README.md) | what the firmware proves and why it lives here, what a release carries, the three identities, building it, changing it | `build_artifacts.py`, `.github/workflows/release.yml`, `.github/workflows/build.yml`, `firmware/platformio.ini` |

For a rig owner the firmware is described in the rig's guide (the "health check firmware" page published from `Alteriom/esp32-rig`); a change here that changes what that page says is followed there.

## Known drift

None found at the verified commit: every claim of `README.md` was checked against `build_artifacts.py` and the two workflows.
