# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses [Semantic Versioning](https://semver.org/) for its own
releases (fittingly, given what it converts).

## [0.1.0] - 2026-09-21

### Added

- `parse_semver` / `format_semver` for parsing and rendering SemVer 2.0.0
  strings.
- `semver_to_pep440` for converting SemVer strings to PEP 440, including
  `alpha`/`beta`/`rc` prerelease mapping and a `dev`/`post` prerelease
  convention for PEP 440's dev- and post-release segments.
- `pep440_to_semver` for the reverse conversion, including recovery of
  prerelease chains longer than a label and a number via the `svN.` local
  version marker.
- `semverconv` command-line tool with `to-pep440` and `to-semver`
  subcommands.
- Type hints and a `py.typed` marker for downstream type checkers.

[0.1.0]: https://github.com/nhall494/semverconv/releases/tag/v0.1.0
