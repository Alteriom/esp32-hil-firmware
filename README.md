# The Rig Health Check firmware

[![Build](https://github.com/Alteriom/esp32-hil-firmware/actions/workflows/build.yml/badge.svg)](https://github.com/Alteriom/esp32-hil-firmware/actions/workflows/build.yml)
[![Release](https://github.com/Alteriom/esp32-hil-firmware/actions/workflows/release.yml/badge.svg)](https://github.com/Alteriom/esp32-hil-firmware/actions/workflows/release.yml)
[![Latest release](https://img.shields.io/github/v/release/Alteriom/esp32-hil-firmware?label=release)](https://github.com/Alteriom/esp32-hil-firmware/releases/latest)
[![Families](https://img.shields.io/badge/families-esp32%20%C2%B7%20c3%20%C2%B7%20c5%20%C2%B7%20c6%20%C2%B7%20s3%20%C2%B7%20esp8266-6b8)](firmware/)
[![PlatformIO](https://img.shields.io/badge/built%20with-PlatformIO-f5822a?logo=platformio&logoColor=white)](https://platformio.org/)
[![Used by esp32-rig](https://img.shields.io/badge/pinned%20by-Alteriom%2Fesp32--rig-555)](https://github.com/Alteriom/esp32-rig/blob/main/canary/firmware.json)
[![License](https://img.shields.io/github/license/Alteriom/esp32-hil-firmware)](LICENSE)

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
  firmware's version, its source digest (`revision`), the commit it belongs
  to, its families, the serial commands it answers (`commands`) and, per
  family, the pins it lets an instrument be wired to (`pins`) -- so a rig
  holds its client, its simulator and its wiring table to the firmware it
  pins without this source;
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
