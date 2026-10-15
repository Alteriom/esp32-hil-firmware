# Shared reference

What every job on this repository draws on. Each file points at the repository file that owns a fact; follow the pointer for the detail, and when the two disagree the owning file is right.

| File | Answers |
|---|---|
| [architecture.md](architecture.md) | the map: the four repositories, the source, the build, the bundle and `firmware.json` |
| [build-and-test.md](build-and-test.md) | how to run the fast checks and build every family, the PlatformIO cores, what CI runs |
| [rules.md](rules.md) | the protocol shared with the rig, the three identities, the source's bytes, public names, conventions |
| [release.md](release.md) | how a version is computed, released by a person, and taken by a rig through its pin |
| [documents.md](documents.md) | the documents a person reads here and who owns their facts |

Each stage's contract names the files it loads.
