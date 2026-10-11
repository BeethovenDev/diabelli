"""CLI tests for DIABELLI."""

from __future__ import annotations

import json
import subprocess
import sys

from diabelli.core import load_manifest


def _run(*argv: str, cwd) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "diabelli", *argv],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_init_writes_manifest(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
    proc = _run("init", ".", cwd=tmp_path)
    assert proc.returncode == 0
    manifest = load_manifest(tmp_path / "diabelli.manifest.json")
    assert "a.txt" in manifest.entries


def test_check_reports_drift_and_exit_1(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("one", encoding="utf-8")
    assert _run("init", ".", cwd=tmp_path).returncode == 0

    (tmp_path / "a.txt").write_text("two!", encoding="utf-8")
    (tmp_path / "new.txt").write_text("n", encoding="utf-8")

    proc = _run("check", cwd=tmp_path)
    assert proc.returncode == 1
    assert "modified" in proc.stdout and "a.txt" in proc.stdout
    assert "added" in proc.stdout and "new.txt" in proc.stdout

    json_proc = _run("--json", "check", cwd=tmp_path)
    payload = json.loads(json_proc.stdout)
    assert payload["clean"] is False
    assert payload["modified"] == ["a.txt"]
    assert payload["added"] == ["new.txt"]


def test_check_clean_exit_0(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("one", encoding="utf-8")
    _run("init", ".", cwd=tmp_path)
    proc = _run("check", cwd=tmp_path)
    assert proc.returncode == 0
    assert "clean" in proc.stdout


def test_check_missing_manifest_exit_2(tmp_path) -> None:
    proc = _run("check", cwd=tmp_path)
    assert proc.returncode == 2
    assert "error" in proc.stderr


def test_check_respects_extra_ignore(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("one", encoding="utf-8")
    _run("init", ".", "--ignore", "*.txt", cwd=tmp_path)
    # manifest now excludes a.txt; re-adding it is invisible when checked with --ignore
    proc = _run("check", "--ignore", "*.txt", cwd=tmp_path)
    assert proc.returncode == 0
