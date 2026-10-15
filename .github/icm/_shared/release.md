---
verified_at: 2026-10-15
verified_commit: 3b25ad9f17f1bd1af0bf2d028804ccf8d69c56d1
---

# Releasing — the tag is the version, the rig's pin is the delivery

## The number

A release is a tag `vMAJOR.MINOR.PATCH`: MAJOR.MINOR is `firmware/VERSION` (moved by hand, in a pull request), PATCH the number of commits that changed `firmware/`. `python build_artifacts.py --version` prints what the tree builds; the step "The tag is the version" of `.github/workflows/release.yml` refuses a tag that disagrees. A commit outside `firmware/` (documentation, workflows, these files) changes neither the number nor `farm_sha`, so it needs no release. The releases page (`gh release list --repo Alteriom/esp32-hil-firmware`) shows the last one.

## Cutting it, by a person

1. Merge to `main` (squash) with `Build` green: the tests and every family.
2. A person tags what the tree says and pushes the tag: `git tag v<version> origin/main && git push origin v<version>`. No agent pushes a tag.
3. `release.yml` builds the six families, packs `alteriom-hil-canary-<version>.tar.gz`, writes `firmware.json` (`build_artifacts.py --describe`) and `SHA256SUMS`, and attaches the three to the GitHub release with notes naming the families. A dispatch against a ref builds and attaches nothing.

## Delivery: the rig's pin

Nothing reaches a rig until `Alteriom/esp32-rig` moves its pin: its `canary/firmware.json` becomes this release's `firmware.json`, copied verbatim, in a reviewed one-line pull request there; the rig's own release then fetches the tarball and checks it against the pin's digest, version, revision and families. A release that changed `commands`, `pins` or the families also needs the rig's suite, simulator or wiring table changed in that pull request or before it ([rules.md](rules.md) "The protocol is shared"). That pull request is the rig's to review; nothing here edits it.
