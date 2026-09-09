"""Command-line entry point for semverconv.

Kept separate from converter.py so the conversion logic stays free of argv,
stdout, and sys.exit -- none of that belongs in a pure-function library.
"""

from __future__ import annotations

import argparse
import sys

from .converter import pep440_to_semver, semver_to_pep440


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="semverconv",
        description="Convert version strings between SemVer 2.0.0 and PEP 440.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    to_pep440 = subparsers.add_parser(
        "to-pep440", help="convert a SemVer string to PEP 440"
    )
    to_pep440.add_argument("version", help="a SemVer 2.0.0 version string")

    to_semver = subparsers.add_parser(
        "to-semver", help="convert a PEP 440 string to SemVer"
    )
    to_semver.add_argument("version", help="a PEP 440 version string")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    convert = semver_to_pep440 if args.command == "to-pep440" else pep440_to_semver
    try:
        print(convert(args.version))
    except ValueError as exc:
        print(f"semverconv: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
