"""Core tests for DIABELLI."""

from __future__ import annotations

import pytest

from diabelli.core import (
    ManifestError,
    compare,
    fingerprint_tree,
    load_manifest,
    manifest_from_tree,
    save_manifest,
)


def _tree(root, spec: dict[str, str]) -> None:
    for name, content in spec.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_fingerprint_tree_counts_files_and_ignores_dirs(tmp_path) -> None:
    _tree(tmp_path, {"a.txt": "alpha", "sub/b.txt": "beta" * 100})
    entries = fingerprint_tree(tmp_path)
    assert set(entries) == {"a.txt", "sub/b.txt"}
    assert all(e.kind == "file" for e in entries.values())
    assert entries["a.txt"].size == 5


def test_sha256_changes_with_content(tmp_path) -> None:
    path = tmp_path / "a.txt"
    path.write_text("one", encoding="utf-8")
    before = fingerprint_tree(tmp_path)["a.txt"].sha256
    path.write_text("two squad", encoding="utf-8")
    after = fingerprint_tree(tmp_path)["a.txt"].sha256
    assert before != after


def test_ignore_globs_and_ignore_file(tmp_path) -> None:
    _tree(tmp_path, {"keep.txt": "k", "cache/x.bin": "x", "secret.tmp": "s"})
    (tmp_path / ".diabellignore").write_text("# comment\n*.tmp\n", encoding="utf-8")
    entries = fingerprint_tree(tmp_path, extra_ignores=["cache/"])
    assert set(entries) == {"keep.txt"}
    assert ".diabellignore" not in entries


def test_manifest_round_trip(tmp_path) -> None:
    _tree(tmp_path, {"a.txt": "alpha"})
    manifest = manifest_from_tree(tmp_path)
    out = tmp_path / "m.json"
    save_manifest(manifest, out)
    loaded = load_manifest(out)
    assert loaded.entries == manifest.entries
    assert loaded.root == manifest.root
    assert loaded.format == 1


def test_load_manifest_rejects_bad_format(tmp_path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"format": 99, "entries": {}}', encoding="utf-8")
    with pytest.raises(ManifestError):
        load_manifest(bad)


def test_compare_reports_added_removed_modified(tmp_path) -> None:
    _tree(tmp_path, {"a.txt": "one", "b.txt": "two"})
    baseline = manifest_from_tree(tmp_path)

    (tmp_path / "a.txt").write_text("ONE!", encoding="utf-8")
    (tmp_path / "b.txt").unlink()
    (tmp_path / "c.txt").write_text("three", encoding="utf-8")

    drift = compare(baseline, manifest_from_tree(tmp_path))
    assert drift.added == ["c.txt"]
    assert drift.removed == ["b.txt"]
    assert drift.modified == ["a.txt"]
    assert not drift.clean


def test_compare_clean_when_unchanged(tmp_path) -> None:
    _tree(tmp_path, {"a.txt": "one"})
    drift = compare(manifest_from_tree(tmp_path), manifest_from_tree(tmp_path))
    assert drift.clean
    assert drift.added == drift.removed == drift.modified == []
