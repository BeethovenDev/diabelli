# Changelog

All notable changes to DIABELLI are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-10-11

### Added

- `diabelli init` — fingerprints one or more trees (SHA-256 per regular file,
  target string per symlink) into `diabelli.manifest.json`.
- `diabelli check` — compares the current tree against the manifest:
  added/removed/modified, human text or `--json`, exit code `1` on drift,
  `2` on a broken manifest. Ready for CI gates.
- `diabelli watch` — a poll loop that prints each drift as it happens.
- Ignore support: globs via `.diabellignore` (comments allowed) plus
  repeatable `--ignore GLOB`.
- `--json` machine-readable output on `init` and `check`.
- Zero runtime dependencies, Python 3.10+, strict mypy and ruff, pytest suite.