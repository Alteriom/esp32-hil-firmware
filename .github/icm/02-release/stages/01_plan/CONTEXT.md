# 01_plan — what changed, and the number

One job: a release plan naming the commit, the version the tree builds, and what changed for a rig.

## Inputs
- Working (this run): the changes since the last release — `gh release list --repo Alteriom/esp32-hil-firmware --limit 3`, then `git log --oneline <last tag>..origin/main -- firmware/`.
- Reference (every run): `.github/icm/_shared/release.md`

Do NOT load: the other pipelines, other runs' output.

## Process
1. List the commits that changed `firmware/` since the last tag. If there are none, there is nothing to release: say so and stop ([release.md](../../../_shared/release.md) "The number").
2. Say what each changes for a rig: a check's behaviour, a family, the `commands` or `pins` in `firmware.json`. A change to those needs the rig's suite, simulator or wiring table to follow.
3. Run `python build_artifacts.py --version` on an up-to-date `origin/main` and confirm the tag does not exist (`git ls-remote --tags origin`). If MAJOR.MINOR should move, that is a pull request to `firmware/VERSION` first.
4. Confirm `Build` is green on that commit for every family; record the run link.
5. Write the exact commands for the person: `git tag v<version> <commit> && git push origin v<version>`.

## Outputs
- plan.md → output/ — the commit and the version; each firmware change and what it means for a rig; the green build run; the commands for the person.

## Human check
A person approves the version and the commit; nothing is tagged until they do.
