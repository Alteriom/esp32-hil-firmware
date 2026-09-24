#!/usr/bin/env python3
"""Build the Rig Health Check firmware: one merged flash image per ESP32 MCU family.

The Rig Health Check is the firmware a rig flashes to prove its own hardware:
that each board boots, its serial path is clean, its flash keeps a value, the
rig can reset it, its radio sees the rig's network. It validates any hardware
the rig supports, so it lives here, on its own, and changes when a family or
a check changes -- not when the rig software does. A rig pins a release of
this repository (`canary/firmware.json` in Alteriom/esp32-rig) and takes the
bundle from it; nothing there compiles firmware.

Three identities travel in the manifest and they answer different questions:

  * `farm_sha`, the commit of this repository the firmware belongs to, is the
    bundle's revision of record (the rig's health check profile reads it
    under that key). It is the last commit that changed `firmware/`, so it
    holds until the firmware changes again.
  * `canary_sha`, the digest of `firmware/`, is the firmware's own identity:
    the same source is the same firmware whatever commit it sits at. A board
    reports it back over serial, so a report can say which firmware answered.
  * `version`, MAJOR.MINOR.PATCH, is the one a person reads. MAJOR.MINOR is
    `firmware/VERSION`, moved by hand; PATCH is the number of commits that
    changed `firmware/`. It is compiled in, so a board reports it too. A
    release of this repository is tagged with exactly this version.

The output is the schema-2 manifest contract the rig verifies at upload and
at flash (`alteriom_hil.artifacts` in the rig): the same one every producer
emits, so the health check is flashed, verified, listed, pinned and pruned by
the machinery that already exists.

    python build_artifacts.py --out hil-canary [--target esp32-c6]
    python build_artifacts.py --version
    python build_artifacts.py --revision
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

FIRMWARE_DIR = Path(__file__).resolve().parent / "firmware"
DEFAULT_OUT = Path(os.environ.get("ALTERIOM_CANARY_ARTIFACT_DIR", "hil-canary"))

# The same families, boards and bootloader offsets as every other producer:
# silicon facts, kept in sync with the esptool defaults.
TARGETS = {
    "esp32": {"chip": "esp32", "board": "esp32dev", "bootloader": "0x1000", "layout": "esp32"},
    "esp32-c3": {"chip": "esp32c3", "board": "esp32-c3-devkitm-1", "bootloader": "0x0", "layout": "esp32"},
    "esp32-c5": {"chip": "esp32c5", "board": "esp32-c5-devkitc-1", "bootloader": "0x2000", "layout": "esp32"},
    "esp32-c6": {"chip": "esp32c6", "board": "esp32-c6-devkitc-1", "bootloader": "0x0", "layout": "esp32"},
    "esp32-s3": {"chip": "esp32s3", "board": "esp32-s3-devkitc-1", "bootloader": "0x0", "layout": "esp32"},
    "esp8266": {"chip": "esp8266", "board": "nodemcuv2", "bootloader": "0x0", "layout": "esp8266"},
}

# One PlatformIO core directory per family, all under one parent: the two
# Arduino cores ship a package of the same name, and in one directory
# whichever installs first keeps it. Override the parent with ALTERIOM_PIO_CORES.
PIO_CORES_DIRNAME = ".platformio-cores"


def core_dir_for(name: str) -> Path:
    root = Path(os.environ.get("ALTERIOM_PIO_CORES") or Path.home() / PIO_CORES_DIRNAME)
    return root / name


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canary_sha() -> str:
    """The digest of the firmware's own source: this bundle's identity.

    Every file under `firmware/`, path and bytes, so a change to the
    platformio.ini that picks a platform counts as much as a change to the
    firmware. A build directory is not source and is skipped.
    """
    digest = hashlib.sha256()
    for path in sorted(FIRMWARE_DIR.rglob("*")):
        if not path.is_file() or ".pio" in path.parts:
            continue
        digest.update(path.relative_to(FIRMWARE_DIR).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def farm_sha() -> str:
    """The commit this firmware belongs to: the bundle's revision of record.

    The last commit that changed `firmware/`, not the checkout's HEAD, so the
    revision holds until the firmware changes again. A shallow checkout whose
    history stops before that commit, and a tree git cannot answer for at
    all, fall back to HEAD and then GITHUB_SHA; if nothing can say, the build
    fails rather than recording a revision it invented.
    """
    for args in (["log", "-1", "--format=%H", "--", str(FIRMWARE_DIR)], ["rev-parse", "HEAD"]):
        try:
            found = subprocess.run(["git", "-C", str(FIRMWARE_DIR), *args],
                                   capture_output=True, text=True, timeout=20)
            if found.returncode == 0 and found.stdout.strip():
                return found.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    fallback = (os.environ.get("GITHUB_SHA") or "").strip()
    if fallback:
        return fallback
    raise RuntimeError(
        "cannot determine the commit this firmware is built from: git could not answer and GITHUB_SHA is unset")


def firmware_version() -> str:
    """MAJOR.MINOR from VERSION, PATCH from the commits that changed the firmware.

    A modified or untracked file under `firmware/` is marked `+modified`: that
    build is not the version it would otherwise claim. A shallow checkout
    counts only the commits it fetched, and git that cannot answer counts
    nothing, so both fail the build rather than stamp a number that looks
    right and is not.
    """
    try:
        base = "".join((FIRMWARE_DIR / "VERSION").read_text(encoding="utf-8").split())
    except OSError as exc:
        raise RuntimeError(f"firmware/VERSION is missing: {exc}") from exc
    if not re.fullmatch(r"\d+\.\d+", base):
        raise RuntimeError(f"firmware/VERSION must be MAJOR.MINOR, not {base!r}")

    def git(*args: str) -> str:
        found = subprocess.run(["git", "-C", str(FIRMWARE_DIR), *args], capture_output=True, text=True, timeout=20)
        if found.returncode != 0:
            raise RuntimeError(f"cannot number the Rig Health Check firmware: git {' '.join(args)} "
                               f"failed: {found.stderr.strip() or found.returncode}")
        return found.stdout.strip()

    try:
        if git("rev-parse", "--is-shallow-repository") == "true":
            raise RuntimeError("cannot number the Rig Health Check firmware from a shallow checkout: "
                               "fetch the full history (actions/checkout fetch-depth: 0)")
        count = int(git("rev-list", "--count", "HEAD", "--", "."))
        modified = bool(git("status", "--porcelain", "--", "."))
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise RuntimeError(f"cannot number the Rig Health Check firmware: {exc}") from exc
    return f"{base}.{count}" + ("+modified" if modified else "")


def normalize_targets(names: list[str] | None) -> list[str]:
    selected = sorted(set(names or TARGETS))
    unknown = set(selected) - set(TARGETS)
    if unknown:
        raise ValueError(f"unsupported target(s): {sorted(unknown)}; expected {sorted(TARGETS)}")
    return selected


def _boot_app0(core_dir: Path) -> Path:
    """The fixed OTA-data image, from the core directory this family built in."""
    candidates = sorted(core_dir.glob("packages/framework-arduinoespressif32*/tools/partitions/boot_app0.bin"))
    if not candidates:
        raise FileNotFoundError(f"PlatformIO boot_app0.bin was not installed under {core_dir}")
    return candidates[0]


def build_artifacts(out_dir: Path, names: list[str] | None = None) -> Path:
    selected = normalize_targets(names)
    pio = shutil.which("pio")
    if not pio:
        raise FileNotFoundError("pio is not on PATH")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    revision = canary_sha()
    commit = farm_sha()
    version = firmware_version()
    build_env = dict(os.environ, CANARY_SHA=revision, CANARY_VERSION=version)
    entries: dict = {}
    for name in selected:
        target = TARGETS[name]
        core_dir = core_dir_for(name)
        print(f"==> Rig Health Check {version} {name} ({target['board']}) in {core_dir}")
        subprocess.run([pio, "run", "-d", str(FIRMWARE_DIR), "-e", name], check=True,
                       env={**build_env, "PLATFORMIO_CORE_DIR": str(core_dir)})
        pio_build = FIRMWARE_DIR / ".pio" / "build" / name
        target_dir = out_dir / name
        target_dir.mkdir(parents=True, exist_ok=True)
        if target["layout"] == "esp8266":
            components = {"firmware.bin": pio_build / "firmware.bin"}
            segments = {"firmware.bin": "0x0"}
        else:
            components = {
                "bootloader.bin": pio_build / "bootloader.bin",
                "partitions.bin": pio_build / "partitions.bin",
                "boot_app0.bin": _boot_app0(core_dir),
                "firmware.bin": pio_build / "firmware.bin",
            }
            segments = {"bootloader.bin": target["bootloader"], "partitions.bin": "0x8000",
                        "boot_app0.bin": "0xe000", "firmware.bin": "0x10000"}
        for filename, source in components.items():
            if not source.is_file():
                raise FileNotFoundError(f"missing build component: {source}")
            shutil.copy2(source, target_dir / filename)
        merged = target_dir / "flash-image.bin"
        if target["layout"] == "esp8266":
            shutil.copy2(target_dir / "firmware.bin", merged)
        else:
            merge = [sys.executable, "-m", "esptool", "--chip", target["chip"], "merge-bin", "-o", str(merged)]
            for filename, offset in segments.items():
                merge.extend((offset, str(target_dir / filename)))
            subprocess.run(merge, check=True)
        files = {path.name: {"sha256": sha256(path), "size": path.stat().st_size}
                 for path in sorted(target_dir.glob("*.bin"))}
        entries[name] = {
            "platformio_env": name, "board": target["board"], "chip": target["chip"],
            "flash_offset": "0x0", "image": f"{name}/flash-image.bin",
            "sha256": files["flash-image.bin"]["sha256"], "files": files, "segments": segments,
        }
    manifest = out_dir / "manifest.json"
    manifest.write_text(json.dumps({
        "schema": 2,
        "producer": "canary",
        "farm_sha": commit,
        "canary_sha": revision,
        "version": version,
        "targets": entries,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Rig Health Check {version} manifest: {manifest}")
    return manifest


def commands() -> list[str]:
    """The serial commands the firmware answers, read from its own dispatch
    chain. They travel in firmware.json so the rig can hold its client and
    its simulator to exactly what the firmware it pins accepts, without the
    source."""
    source = (FIRMWARE_DIR / "src" / "main.cpp").read_text(encoding="utf-8")
    return sorted(set(re.findall(r'strcmp\(name, "([a-z_]+)"\) == 0', source)))


# The preprocessor branch each family's pin table sits under in
# canary_platform.h, in the order they appear. The ESP32's is matched with
# its newline so it is not the prefix of the C3's, C6's or S3's.
PIN_TABLE_BRANCHES = {
    "esp8266": "defined(ESP8266)",
    "esp32-c3": "defined(CONFIG_IDF_TARGET_ESP32C3)",
    "esp32-c6": "defined(CONFIG_IDF_TARGET_ESP32C6)",
    "esp32-s3": "defined(CONFIG_IDF_TARGET_ESP32S3)",
    "esp32": "defined(CONFIG_IDF_TARGET_ESP32)\n",
}


def pins() -> dict[str, dict[str, list[int]]]:
    """The pins an instrument may be wired to, per family, read from the
    firmware's own tables (canary_platform.h): the ones the wiring check may
    drive or read, and the input-only ones among them. They travel in
    firmware.json so a rig can hold its wiring table to the firmware it
    pins, without the source. A family with no table is absent -- never
    given another's."""
    source = (FIRMWARE_DIR / "src" / "canary_platform.h").read_text(encoding="utf-8")
    source = source.split("the pins an instrument may be wired to", 1)[1]
    tables: dict[str, dict[str, list[int]]] = {}
    for family, condition in PIN_TABLE_BRANCHES.items():
        block = source.split(condition, 1)[1].split("#e", 1)[0]
        if f'kPinTable = "pins:{family}"' not in block:
            raise RuntimeError(f"canary_platform.h names no pin table for {family}")

        def numbers(name: str) -> list[int]:
            found = re.search(rf"{name}\[\] = \{{([^}}]*)\}}", block)
            if not found:
                raise RuntimeError(f"canary_platform.h has no {name} for {family}")
            values = [int(n) for n in found.group(1).split(",")]
            if values[-1] != -1:
                raise RuntimeError(f"{name} for {family} does not end in -1")
            return values[:-1]

        tables[family] = {"wireable": numbers("kWireablePins"), "input_only": numbers("kInputOnlyPins")}
    return dict(sorted(tables.items()))


def describe(out_dir: Path, tarball: Path) -> dict:
    """`firmware.json`: what a rig pins -- the tarball by name and digest, the
    firmware by version, revision and families, the commands it answers and
    the pins it lets an instrument be wired to."""
    built = json.loads((Path(out_dir) / "manifest.json").read_text(encoding="utf-8"))
    return {
        "schema": 1,
        "name": tarball.name,
        "sha256": sha256(tarball),
        "bytes": tarball.stat().st_size,
        "version": str(built["version"]),
        "revision": str(built["canary_sha"]),
        "commit": str(built["farm_sha"]),
        "families": sorted(built["targets"]),
        "commands": commands(),
        "pins": pins(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--target", action="append", choices=sorted(TARGETS))
    parser.add_argument("--revision", action="store_true", help="print the firmware's source digest and build nothing")
    parser.add_argument("--version", action="store_true", dest="print_version",
                        help="print the firmware version this checkout builds, and build nothing")
    parser.add_argument("--describe", type=Path, metavar="TARBALL",
                        help="print firmware.json for a bundle already built into --out and packed as TARBALL")
    args = parser.parse_args(argv)
    if args.print_version:
        print(firmware_version())
        return 0
    if args.revision:
        print(canary_sha())
        return 0
    if args.describe:
        print(json.dumps(describe(args.out, args.describe), indent=2, sort_keys=True))
        return 0
    build_artifacts(args.out, args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
