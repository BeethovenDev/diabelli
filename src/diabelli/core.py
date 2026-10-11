"""DIABELLI core: manifest fingerprints, traversal and drift comparison.

Fingerprints are content-based (SHA-256) — a file that changed content is a
variation, no matter what its mtime claims. Symlinks are recorded by their
target string, not followed. Directories are deliberately omitted: their mtime
changes are noise.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

__all__ = [
    "Drift",
    "Entry",
    "ManifestError",
    "compare",
    "fingerprint_tree",
    "load_manifest",
    "save_manifest",
]

MANIFEST_FORMAT = 1
IGNORE_FILENAME = ".diabellignore"


class ManifestError(Exception):
    """Raised when a manifest is missing, unreadable or inconsistent."""


@dataclass(frozen=True)
class Entry:
    rel: str
    sha256: str
    size: int
    mtime: int
    kind: str  # "file" | "symlink"


@dataclass(frozen=True)
class Manifest:
    tool: str
    version: str
    format: int
    root: str
    entries: dict[str, Entry]


@dataclass
class Drift:
    added: list[str]
    removed: list[str]
    modified: list[str]

    @property
    def clean(self) -> bool:
        return not (self.added or self.removed or self.modified)


def _read_ignore_lines(root: Path) -> list[str]:
    ignore_file = root / IGNORE_FILENAME
    if not ignore_file.is_file():
        return []
    lines = [
        line.strip()
        for line in ignore_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    # always ignore the ignore-file and the manifest itself
    lines.append(IGNORE_FILENAME)
    return lines


def _ignored(rel: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        # "cache/" should also cover everything beneath it
        stripped = pattern.rstrip("/")
        if (
            fnmatch.fnmatch(rel, pattern)
            or fnmatch.fnmatch(rel, stripped + "/*")
            or fnmatch.fnmatch(rel, stripped + "/**")
        ):
            return True
    return False


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint_tree(root: Path, extra_ignores: list[str] | None = None) -> dict[str, Entry]:
    """Walk ``root`` and fingerprint every regular file and symlink."""
    if not root.is_dir():
        raise ManifestError(f"not a directory: {root}")
    patterns = list(extra_ignores or [])
    patterns += _read_ignore_lines(root)

    entries: dict[str, Entry] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # prevent recursion through symlinked directories
        dirnames[:] = [d for d in dirnames if not (Path(dirpath) / d).is_symlink()]
        for filename in filenames:
            path = Path(dirpath) / filename
            rel = path.relative_to(root).as_posix()
            if _ignored(rel, patterns):
                continue
            if path.is_symlink():
                target = os.readlink(path)
                stat = path.lstat()
                entries[rel] = Entry(
                    rel=rel,
                    sha256=_sha256(target.encode("utf-8")),
                    size=stat.st_size,
                    mtime=int(stat.st_mtime),
                    kind="symlink",
                )
                continue
            if not path.is_file():
                continue
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(chunk)
            entries[rel] = Entry(
                rel=rel,
                sha256=digest.hexdigest(),
                size=path.stat().st_size,
                mtime=int(path.stat().st_mtime),
                kind="file",
            )
    return entries


def manifest_from_tree(
    root: Path,
    extra_ignores: list[str] | None = None,
    tool: str = "diabelli",
    version: str = "0.1.0",
) -> Manifest:
    return Manifest(
        tool=tool,
        version=version,
        format=MANIFEST_FORMAT,
        root=str(root.resolve()),
        entries=fingerprint_tree(root, extra_ignores),
    )


def save_manifest(manifest: Manifest, path: Path) -> None:
    payload = {
        "tool": manifest.tool,
        "version": manifest.version,
        "format": manifest.format,
        "root": manifest.root,
        "entries": {
            rel: asdict(entry)
            for rel, entry in sorted(manifest.entries.items())
        },
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_manifest(path: Path) -> Manifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read manifest {path}: {exc}") from exc
    if raw.get("format") != MANIFEST_FORMAT:
        raise ManifestError(f"unsupported manifest format: {raw.get('format')!r}")
    entries: dict[str, Entry] = {}
    for rel, entry in raw["entries"].items():
        entries[rel] = Entry(
            rel=rel,
            sha256=entry["sha256"],
            size=int(entry["size"]),
            mtime=int(entry["mtime"]),
            kind=entry["kind"],
        )
    return Manifest(
        tool=raw.get("tool", "unknown"),
        version=raw.get("version", "0"),
        format=int(raw["format"]),
        root=str(raw["root"]),
        entries=entries,
    )


def compare(baseline: Manifest, current: Manifest) -> Drift:
    base_keys = set(baseline.entries)
    cur_keys = set(current.entries)
    added = sorted(cur_keys - base_keys)
    removed = sorted(base_keys - cur_keys)
    modified = sorted(
        rel
        for rel in base_keys & cur_keys
        if baseline.entries[rel].sha256 != current.entries[rel].sha256
        or baseline.entries[rel].kind != current.entries[rel].kind
    )
    return Drift(added=added, removed=removed, modified=modified)
