"""What the firmware source promises, asserted rather than trusted.

Each of these came from a rig: a red health check that was the firmware's
own bug -- a truncated line on a native USB console, a timeout in the wrong
units, a read loop that gave up before the answer arrived -- and the rule
that the health check depends on nothing a consumer ships, which is what
makes a red canary never somebody's regression.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_artifacts  # noqa: E402

FIRMWARE_DIR = ROOT / "firmware"
MAIN = FIRMWARE_DIR / "src" / "main.cpp"
SHIM = FIRMWARE_DIR / "src" / "canary_platform.h"


def test_the_firmware_carries_no_consumer_code():
    """Against what it depends on, not against its prose."""
    sources = [path for path in FIRMWARE_DIR.rglob("*") if path.is_file() and ".pio" not in path.parts]
    assert sources, "the firmware source is missing"
    code = "\n".join(path.read_text(encoding="utf-8") for path in sources if path.suffix in (".cpp", ".h"))
    includes = set(re.findall(r'#include\s+[<"]([^>"]+)[>"]', code))
    allowed = {"Arduino.h", "ArduinoJson.h", "canary_platform.h",
               "ESP8266WiFi.h", "LittleFS.h", "Preferences.h", "WiFi.h", "esp_system.h"}
    assert includes and includes <= allowed, f"unexpected dependency: {sorted(includes - allowed)}"
    ini = (FIRMWARE_DIR / "platformio.ini").read_text(encoding="utf-8")
    declared = re.findall(r"^ {4}([A-Za-z0-9@/._-]+=?[^\r\n]*)$", ini, re.MULTILINE)
    libraries = [entry.strip() for entry in declared if "/" in entry and not entry.startswith("-D") and "://" not in entry]
    assert libraries == ["bblanchon/ArduinoJson@7.4.3"], libraries
    assert "symlink://" not in ini and "file://" not in ini


def _verify_like_a_rig(out: Path) -> dict:
    """What a rig's loader checks at upload and at flash: every image's
    digest, every component at its stated offset inside the merged image."""
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == 2
    for name, entry in manifest["targets"].items():
        image = out / entry["image"]
        assert image.is_file(), image
        assert hashlib.sha256(image.read_bytes()).hexdigest() == entry["sha256"], name
        merged = image.read_bytes()
        for filename, offset in entry["segments"].items():
            component = (out / name / filename).read_bytes()
            assert hashlib.sha256(component).hexdigest() == entry["files"][filename]["sha256"], f"{name}/{filename}"
            at = int(offset, 0)
            assert merged[at:at + len(component)] == component, f"{name}/{filename} at {offset}"
    return manifest


def test_the_build_writes_the_manifest_contract_every_producer_does(tmp_path, monkeypatch):
    """A bundle a rig can flash, verify, list, pin and prune satisfies the
    schema-2 manifest contract; the verification here is the rig's."""
    out = tmp_path / "hil-canary"
    firmware_dir = tmp_path / "firmware"
    firmware_dir.mkdir()
    (firmware_dir / "VERSION").write_text("1.0\n", encoding="utf-8")
    monkeypatch.setattr(build_artifacts, "FIRMWARE_DIR", firmware_dir)

    def fake_pio(argv, check=True, env=None, **kwargs):
        if argv[0] == "pio":
            name = argv[argv.index("-e") + 1]
            built = firmware_dir / ".pio" / "build" / name
            built.mkdir(parents=True, exist_ok=True)
            for filename, body in (("firmware.bin", b"\xe9" + name.encode()), ("bootloader.bin", b"\xe9boot"),
                                   ("partitions.bin", b"partitions")):
                (built / filename).write_bytes(body)
            assert env["CANARY_SHA"] == build_artifacts.canary_sha(), "built with its own digest compiled in"
            assert env["CANARY_VERSION"] == "1.0.42", "built with its version compiled in"
            return subprocess.CompletedProcess(argv, 0)
        rest = argv[argv.index("-o") + 1:]
        target, pairs = Path(rest[0]), rest[1:]
        image = bytearray()
        for offset, source in zip(pairs[::2], pairs[1::2]):
            at = int(offset, 16)
            if len(image) < at:
                image.extend(b"\xff" * (at - len(image)))
            body = Path(source).read_bytes()
            image[at:at + len(body)] = body
        target.write_bytes(bytes(image))
        return subprocess.CompletedProcess(argv, 0)

    boot_app0 = tmp_path / "boot_app0.bin"
    boot_app0.write_bytes(b"boot_app0")
    monkeypatch.setattr(build_artifacts.shutil, "which", lambda name: name)
    monkeypatch.setattr(build_artifacts.subprocess, "run", fake_pio)
    monkeypatch.setattr(build_artifacts, "_boot_app0", lambda core: boot_app0)
    monkeypatch.setattr(build_artifacts, "farm_sha", lambda: "b" * 40)
    monkeypatch.setattr(build_artifacts, "firmware_version", lambda: "1.0.42")
    manifest_path = build_artifacts.build_artifacts(out, ["esp32", "esp32-c6", "esp8266"])
    manifest = _verify_like_a_rig(out)
    assert manifest_path == out / "manifest.json"
    assert manifest["producer"] == "canary" and manifest["farm_sha"] == "b" * 40
    assert re.fullmatch(r"[0-9a-f]{64}", manifest["canary_sha"]) and manifest["version"] == "1.0.42"
    assert sorted(manifest["targets"]) == ["esp32", "esp32-c6", "esp8266"]
    for name, entry in manifest["targets"].items():
        assert entry["image"] == f"{name}/flash-image.bin" and entry["flash_offset"] == "0x0"
        assert entry["board"] and entry["chip"] and entry["platformio_env"] == name
    assert manifest["targets"]["esp8266"]["segments"] == {"firmware.bin": "0x0"}
    assert manifest["targets"]["esp32"]["segments"]["bootloader.bin"] == "0x1000"
    assert manifest["targets"]["esp32-c6"]["segments"]["bootloader.bin"] == "0x0"


def test_the_firmware_reads_a_whole_line_before_it_sleeps():
    """A native USB-Serial/JTAG console starts with a 256-byte receive buffer,
    and the loop slept in the middle of a kilobyte-long command arriving."""
    shim = SHIM.read_text(encoding="utf-8")
    firmware = MAIN.read_text(encoding="utf-8")
    assert "setRxBufferSize" in shim and "console.begin(115200)" in shim
    assert "canaryOpenConsole(Serial, kLineMax + 512)" in firmware
    assert "Serial.begin(115200)" not in firmware, "the console is opened with room"
    assert "bool pump(Stream &console)" in firmware
    assert "if (!busy) delay(2);" in firmware


def test_a_tcp_timeout_is_in_the_units_each_core_means():
    """WiFiClient::setTimeout is seconds on the ESP32 cores and milliseconds
    on the ESP8266; passing seconds to the ESP8266 gave a connect eight
    milliseconds."""
    shim = SHIM.read_text(encoding="utf-8")
    firmware = MAIN.read_text(encoding="utf-8")
    helper = shim.split("inline void canarySetClientTimeout", 1)[1].split(chr(10) + chr(125), 1)[0]
    assert "defined(ESP8266)" in helper
    assert "client.setTimeout(budgetMs);" in helper, "milliseconds on the 8266"
    assert "budgetMs / 1000" in helper, "seconds on the ESP32 cores"
    assert "canarySetClientTimeout(client, budget)" in firmware
    assert "client.setTimeout(" not in firmware


def test_the_uplink_check_waits_for_the_answer_not_the_connection():
    """A server that answers and closes leaves connected() false with the
    answer still in the buffer; a read loop gated on it reads nothing."""
    firmware = MAIN.read_text(encoding="utf-8")
    body = firmware.split("void replyHttpGet", 1)[1].split("namespace mqtt", 1)[0]
    assert "client.readStringUntil" in body
    reads = body.split("client.print(", 1)[1]
    assert "client.connected()" not in reads


def test_the_commands_are_the_dispatch_chain():
    """What firmware.json says the firmware answers is read from its own
    dispatch, so the list cannot drift from the code."""
    listed = build_artifacts.commands()
    assert {"info", "echo"} <= set(listed)
    source = MAIN.read_text(encoding="utf-8")
    assert set(listed) == set(re.findall(r'strcmp\(name, "([a-z_]+)"\) == 0', source))
