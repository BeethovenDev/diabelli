<div align="center">

# DIABELLI

**File integrity watch — know the instant a tree changes.**

*Named after Beethoven's *33 Variations on a Waltz by Diabelli*: one humble
theme, thirty-three transformations. DIABELLI watches one theme — your
directory — and accounts for every variation.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](#philosophy)

</div>

---

DIABELLI fingerprints a tree once, then tells you the moment anything in it is
added, removed or modified — by SHA-256 content hash, not by trusting mtimes.
Local, offline, zero dependencies, and small enough to run as a CI gate.

Use it to watch release assets, a data directory, a research archive, or an
OSINT corpus whose provenance you want to prove later.

## Install

```bash
git clone https://github.com/BeethovenDev/diabelli.git
cd diabelli
python -m pip install -e .
```

## Quick start

```bash
# 1. fingerprint the tree once
diabelli init data/ -o data.manifest.json

# 2a. ask (text)
diabelli check -m data.manifest.json

# 2b. ask (JSON, for scripts / CI)
diabelli --json check -m data.manifest.json

# 2c. keep watching
diabelli watch -m data.manifest.json --poll 2
```

Exit codes for `check`: **0** clean · **1** drift · **2** manifest broken.
That makes a one-line CI gate:

```bash
diabelli check -m data.manifest.json || exit 1
```

## Ignoring noise

Ignore lines live in `.diabellignore` inside the root (comments with `#`), and
repeatable `--ignore GLOB` flags add more:

```text
# .diabellignore
*.tmp
cache/
*.log
```

## How it works

```
tree ──init──▶ diabelli.manifest.json          (tool, root, format, entries)
                     │
tree ──check─────────┘  sha256 per file, target-string per symlink
                     │
                     ▼
         added / removed / modified  →  exit 0 | 1 | 2
```

* Directories are deliberately not fingerprinted: their mtime churn is noise.
* Symlinks are recorded by their target, never followed.
* Files are compared by content hash only — mtime is recorded for information.

## Philosophy

* **Content over claims.** A file that changed bytes is a variation, whatever
  its modification time says.
* **No surveillance.** Nothing is sent anywhere; the manifest is a local
  snapshot you chose to make.
* **Small enough to trust.** One tiny core, fully reviewed, strict mypy/ruff,
  a pytest suite that builds real trees.

## License

MIT