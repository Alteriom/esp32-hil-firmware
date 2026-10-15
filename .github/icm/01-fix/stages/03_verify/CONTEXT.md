# 03_verify — every family built, the pull request

One job: the pull request a reviewer can merge, with every family built and the bundle verified the way a rig does.

## Inputs
- Working (this run): `.github/icm/01-fix/stages/02_fix/output/change.md`
- Reference (every run): `.github/icm/_shared/build-and-test.md`

Do NOT load: the other pipelines, other runs' output.

## Process
1. Run `python -m pytest -q` and, where the toolchains fit, `python build_artifacts.py --out hil-canary`; otherwise say that `build.yml` will build every family, and read its result after pushing ([build-and-test.md](../../../_shared/build-and-test.md)).
2. Update `README.md` if the change made a line there wrong.
3. Write the pull request: what was wrong, how you know, what the change does, the checks and results, what only a rig run can prove, and that rigs get it after a release here and the pin moving in `Alteriom/esp32-rig`. For a protocol change, link the rig's matching pull request or issue.
4. After the human check, open it against `main` (`gh pr create --base main --body-file <this stage's output/pull-request.md>`). The agent never merges.

## Outputs
- pull-request.md → output/ — the title and body; the checks run with results; the rig change it needs, if any.

## Human check
A person reads `pull-request.md` and the `build.yml` result for every family, and says whether to open it; the reviewer merges.
