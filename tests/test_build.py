"""What the build stamps, and how it numbers itself, without a compiler.

The point of these is that a bundle's three identities are decided by the
source and its history alone: the same source is the same firmware at any
commit, the version moves only when the firmware does, and a build that
cannot say what it is fails rather than guessing.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_artifacts  # noqa: E402


def _firmware_repo(tmp_path: Path, version: str = "1.0") -> Path:
    """A repository shaped like this one: a firmware directory with a VERSION,
    two commits that change it and one that does not."""
    work = tmp_path / "fw"
    firmware = work / "firmware"
    firmware.mkdir(parents=True)

    def git(*args):
        return subprocess.run(["git", *args], cwd=work, check=True, capture_output=True, text=True)

    git("init", "--quiet", "-b", "main")
    git("config", "user.email", "firmware@example.invalid")
    git("config", "user.name", "firmware")
    (firmware / "VERSION").write_text(version + "\n", encoding="utf-8")
    (firmware / "main.cpp").write_text("// one\n", encoding="utf-8")
    git("add", "-A"); git("commit", "--quiet", "-m", "firmware")
    (work / "README.md").write_text("docs\n", encoding="utf-8")
    git("add", "-A"); git("commit", "--quiet", "-m", "not the firmware")
    (firmware / "main.cpp").write_text("// two\n", encoding="utf-8")
    git("add", "-A"); git("commit", "--quiet", "-m", "firmware again")
    return firmware


def test_this_checkout_numbers_itself():
    """VERSION is MAJOR.MINOR and the tree counts its own commits: the number
    a release tag must match."""
    version = build_artifacts.firmware_version()
    assert version.count(".") == 2 and all(part.isdigit() for part in version.split("+")[0].split("."))
    assert len(build_artifacts.canary_sha()) == 64
    assert len(build_artifacts.farm_sha()) == 40


def test_the_source_digest_is_the_firmware_s_identity(tmp_path, monkeypatch):
    """Every file under firmware/, path and bytes; a build directory is not
    source and a rebuild in place must not change what the firmware is."""
    firmware = _firmware_repo(tmp_path)
    monkeypatch.setattr(build_artifacts, "FIRMWARE_DIR", firmware)
    before = build_artifacts.canary_sha()
    stray = firmware / ".pio" / "build" / "esp32" / "firmware.bin"
    stray.parent.mkdir(parents=True)
    stray.write_bytes(b"\xe9 built")
    assert build_artifacts.canary_sha() == before
    (firmware / "main.cpp").write_text("// three\n", encoding="utf-8")
    assert build_artifacts.canary_sha() != before


def test_the_firmware_belongs_to_the_commit_that_last_changed_it(tmp_path, monkeypatch):
    firmware = _firmware_repo(tmp_path)
    monkeypatch.setattr(build_artifacts, "FIRMWARE_DIR", firmware)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=firmware, check=True, capture_output=True, text=True).stdout.strip()
    assert build_artifacts.farm_sha() == head, "the newest commit changed the firmware"
    (firmware.parent / "README.md").write_text("docs again\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=firmware, check=True, capture_output=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "not the firmware either"], cwd=firmware, check=True, capture_output=True)
    assert build_artifacts.farm_sha() == head, "HEAD moved; the firmware did not"


def test_the_version_counts_only_the_commits_that_changed_the_firmware(tmp_path, monkeypatch):
    firmware = _firmware_repo(tmp_path)
    monkeypatch.setattr(build_artifacts, "FIRMWARE_DIR", firmware)
    assert build_artifacts.firmware_version() == "1.0.2", "two of the three commits changed the firmware"
    (firmware / "main.cpp").write_text("// uncommitted\n", encoding="utf-8")
    assert build_artifacts.firmware_version() == "1.0.2+modified"
    subprocess.run(["git", "checkout", "--", "main.cpp"], cwd=firmware, check=True, capture_output=True)
    (firmware / "VERSION").write_text("2.1\n", encoding="utf-8")
    subprocess.run(["git", "commit", "--quiet", "-am", "2.1"], cwd=firmware, check=True, capture_output=True)
    assert build_artifacts.firmware_version() == "2.1.3", "MAJOR.MINOR moved by hand, PATCH keeps counting"


def test_a_version_that_cannot_be_known_is_refused(tmp_path, monkeypatch):
    firmware = _firmware_repo(tmp_path)
    monkeypatch.setattr(build_artifacts, "FIRMWARE_DIR", firmware)
    (firmware / "VERSION").write_text("1\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="MAJOR.MINOR"):
        build_artifacts.firmware_version()
    (firmware / "VERSION").unlink()
    with pytest.raises(RuntimeError, match="VERSION is missing"):
        build_artifacts.firmware_version()


def test_the_commit_is_required_rather_than_invented(monkeypatch):
    monkeypatch.setattr(build_artifacts.subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a[0] if a else [], 128, stdout=""))
    monkeypatch.setenv("GITHUB_SHA", "c" * 40)
    assert build_artifacts.farm_sha() == "c" * 40
    monkeypatch.delenv("GITHUB_SHA")
    with pytest.raises(RuntimeError, match="cannot determine the commit"):
        build_artifacts.farm_sha()


def test_firmware_json_names_what_a_rig_pins(tmp_path):
    out = tmp_path / "hil-canary"
    (out / "esp32").mkdir(parents=True)
    (out / "esp32" / "flash-image.bin").write_bytes(b"\xe9 image")
    (out / "manifest.json").write_text(json.dumps({
        "schema": 2, "producer": "canary", "farm_sha": "a" * 40, "canary_sha": "b" * 64, "version": "1.0.7",
        "targets": {"esp32": {"image": "esp32/flash-image.bin", "sha256": "x", "files": {}, "segments": {}}},
    }), encoding="utf-8")
    tarball = tmp_path / "alteriom-hil-canary-1.0.7.tar.gz"
    tarball.write_bytes(b"not really a tarball, but bytes with a digest")
    described = build_artifacts.describe(out, tarball)
    assert described == {
        "schema": 1, "name": "alteriom-hil-canary-1.0.7.tar.gz", "sha256": build_artifacts.sha256(tarball),
        "bytes": tarball.stat().st_size, "version": "1.0.7", "revision": "b" * 64, "commit": "a" * 40,
        "families": ["esp32"], "commands": build_artifacts.commands(),
    }
    # The commands travel with the pin: what the firmware dispatches on, so a
    # rig can hold its client and simulator to them without the source.
    assert {"info", "echo"} <= set(described["commands"])
    source = (ROOT / "firmware" / "src" / "main.cpp").read_text(encoding="utf-8")
    for command in described["commands"]:
        assert f'strcmp(name, "{command}") == 0' in source


def test_the_targets_are_the_families_a_rig_supports():
    assert set(build_artifacts.TARGETS) == {"esp32", "esp32-c3", "esp32-c5", "esp32-c6", "esp32-s3", "esp8266"}
    with pytest.raises(ValueError, match="unsupported target"):
        build_artifacts.normalize_targets(["esp32", "stm32"])
    ini = (ROOT / "firmware" / "platformio.ini").read_text(encoding="utf-8")
    for family in build_artifacts.TARGETS:
        assert f"[env:{family}]" in ini, family
