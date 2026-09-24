# The Rig Health Check firmware

The firmware an [Alteriom HIL rig](https://github.com/Alteriom/esp32-rig)
flashes to prove its own hardware: that each board boots, its serial path is
clean, its flash keeps a value, the rig can reset it, its radio sees the rig's
network. One image per ESP32 family — esp32, esp32-c3, esp32-c5, esp32-c6,
esp32-s3 — and one for the esp8266, built from `firmware/` with PlatformIO.

It lives here, on its own, because it validates any hardware the rig supports
and changes when a family or a check changes, not when the rig software does.
A rig **pins** a release of this repository (`canary/firmware.json` in the rig)
and takes the bundle from it; the rig's own release compiles nothing.

## What a release is

A tag `vMAJOR.MINOR.PATCH` where `MAJOR.MINOR` is `firmware/VERSION` (moved by
hand) and `PATCH` is the number of commits that changed `firmware/`
(`python build_artifacts.py --version` says what the tree builds; the release
refuses a tag that disagrees). The release carries:

- `alteriom-hil-canary-<version>.tar.gz` — the bundle: `manifest.json` (schema
  2) and, per family, the merged `flash-image.bin` and its components;
- `firmware.json` — what a rig pins: the tarball's name, digest and size, the
  firmware's version, its source digest (`revision`), the commit it belongs to
  and its families;
- `SHA256SUMS`.

Three identities travel in the manifest: `farm_sha`, the commit of this
repository the firmware belongs to (the last one that changed `firmware/`, so
it holds until the firmware changes again); `canary_sha`, the digest of
`firmware/`, which a board reports back over serial; and `version`, the number
a person reads, compiled in.

## Building it yourself

```bash
python -m pip install platformio esptool
python build_artifacts.py --out hil-canary           # every family
python build_artifacts.py --out hil-canary --target esp32-c6
```

Each family builds in its own PlatformIO core directory under
`~/.platformio-cores/` (`ALTERIOM_PIO_CORES` to move it): the two Arduino
cores ship a package of the same name and cannot share one.

## Changing it

Change `firmware/`, open a pull request; the build compiles every family and
verifies the bundle the way a rig does. Merge, tag the version the tree says,
and the release attaches the bundle. The rig takes it by moving its pin — one
reviewed line in `Alteriom/esp32-rig`. The health check *suite* (the tests
that drive this firmware over serial) stays with the rig, under
`suites/canary`; the protocol they share is described in `firmware/src` and
checked there.

Apache-2.0.
