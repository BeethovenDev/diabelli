"""DIABELLI command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from diabelli import BANNER, __version__
from diabelli.core import (
    Manifest,
    ManifestError,
    compare,
    load_manifest,
    manifest_from_tree,
    save_manifest,
)

__all__ = ["main"]

DEFAULT_MANIFEST = "diabelli.manifest.json"


def _emit_json(payload: object) -> None:
    print(json.dumps(payload, indent=2))


def cmd_init(args: argparse.Namespace) -> int:
    roots = [Path(p) for p in args.paths]
    out = Path(args.out)
    last = None
    for root in roots:
        # the manifest itself lives inside the tree it describes
        manifest = manifest_from_tree(root, extra_ignores=[out.name, *args.ignore])
        save_manifest(manifest, out)
        last = manifest
    assert last is not None
    if not args.json:
        print(f"fingerprinted {len(last.entries)} entries from {len(roots)} root(s) -> {out}")
    else:
        _emit_json({"entries": len(last.entries), "manifest": str(out)})
    return 0


def _load(manifest_path: str) -> tuple[Manifest, Path]:
    path = Path(manifest_path)
    try:
        return load_manifest(path), path
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def cmd_check(args: argparse.Namespace) -> int:
    baseline, path = _load(args.manifest)
    root = Path(baseline.root)
    try:
        current = manifest_from_tree(root, extra_ignores=[path.name, *args.ignore])
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    drift = compare(baseline, current)

    if not args.json:
        actions: list[str] = []
        for rel in drift.added:
            actions.append(f"added     {rel}")
        for rel in drift.removed:
            actions.append(f"removed   {rel}")
        for rel in drift.modified:
            actions.append(f"modified  {rel}")

        if actions:
            print(f"drift detected against {path.name} ({len(baseline.entries)} entries):")
            for action in actions:
                print(f"  {action}")
        else:
            print(f"clean — {len(current.entries)} entries match {path.name}")
    else:
        _emit_json(
            {
                "clean": drift.clean,
                "baseline": str(path),
                "added": drift.added,
                "removed": drift.removed,
                "modified": drift.modified,
                "entries": len(current.entries),
            }
        )
    return 0 if drift.clean else 1


def cmd_watch(args: argparse.Namespace) -> int:
    baseline, path = _load(args.manifest)
    root = Path(baseline.root)
    poll = max(1.0, args.poll)
    print(f"watching {root} against {path.name} every {poll:g}s — Ctrl+C to stop")
    try:
        while True:
            drift = compare(baseline, manifest_from_tree(root, extra_ignores=args.ignore))
            if drift.clean:
                print(".", end="", flush=True)
            else:
                print()
                for rel in drift.added:
                    print(f"  added     {rel}")
                for rel in drift.removed:
                    print(f"  removed   {rel}")
                for rel in drift.modified:
                    print(f"  modified  {rel}")
            time.sleep(poll)
    except KeyboardInterrupt:
        print("\nwatcher stopped")
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diabelli",
        description="File integrity watch — treat every change as a variation to account for.",
        epilog="Repo: https://github.com/BeethovenDev/diabelli",
    )
    parser.add_argument("--version", action="version", version=f"diabelli {__version__}")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="fingerprint one or more trees into a manifest")
    p_init.add_argument("paths", nargs="+", metavar="PATH")
    p_init.add_argument("-o", "--out", default=DEFAULT_MANIFEST, metavar="MANIFEST.json")
    p_init.add_argument("--ignore", action="append", default=[], metavar="GLOB",
                        help="extra glob to ignore (repeatable)")
    p_init.set_defaults(func=cmd_init)

    p_check = sub.add_parser("check", help="compare the current tree against the manifest")
    p_check.add_argument("-m", "--manifest", default=DEFAULT_MANIFEST, metavar="MANIFEST.json")
    p_check.add_argument("--ignore", action="append", default=[], metavar="GLOB",
                         help="extra glob to ignore (repeatable)")
    p_check.set_defaults(func=cmd_check)

    p_watch = sub.add_parser("watch", help="poll the tree and print drifts as they happen")
    p_watch.add_argument("-m", "--manifest", default=DEFAULT_MANIFEST, metavar="MANIFEST.json")
    p_watch.add_argument("--ignore", action="append", default=[], metavar="GLOB")
    p_watch.add_argument("--poll", type=float, default=5.0, metavar="SEC")
    p_watch.set_defaults(func=cmd_watch)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    print(BANNER, file=sys.stderr)
    try:
        return int(args.func(args))
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
