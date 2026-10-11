# Security policy

## Scope

DIABELLI is a local integrity watch: it makes **no network calls** and stores
nothing but the `diabelli.manifest.json` you asked it to write. The manifest is
plain JSON — treat it as sensitive if the tree it describes is sensitive.

## Reporting a vulnerability

Do **not** open a public issue for a security problem. Report it privately via
GitHub's [Security Advisories] for this repository.

- Include the version, platform and Python version.
- Include a minimal reproduction. If the reproduction involves a manifest, use
  generated placeholder hashes, not a real tree.
- Every report is acknowledged within 5 business days.

## Notes for users

- Content hashing is SHA-256, computed streaming in 1 MiB chunks — designed for
  size, not for hostile collisions. If your threat model needs a stronger
  digest, that is a feature request, not a promise already made.
- The manifest is not encrypted. On disk, it is as readable as a file listing.
- `diabellignore` patterns are matched with `fnmatch` against relative posix
  paths; they are for noise control, not security boundaries.

[Security Advisories]: https://github.com/BeethovenDev/diabelli/security/advisories