"""Convert Semantic Versioning 2.0.0 strings to PEP 440 version strings.

Every function here is pure: same input always gives the same output, and
nothing is read from or written to the outside world. That makes the whole
module trivial to unit test and safe to call from anywhere (build scripts,
CI, a CLI, whatever ends up calling it later).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# From the official grammar at semver.org/#is-there-a-suggested-regular-expression-in-perl-compatible-regular-expressions-pcre-to-check-a-semver-string
_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

# Non-alphanumeric runs get collapsed to a single "." in PEP 440 local
# version labels (the spec only allows letters, digits, and periods there).
_LOCAL_SEGMENT_RE = re.compile(r"[^0-9a-zA-Z]+")

# SemVer prerelease label -> PEP 440 prerelease letter(s).
_PRERELEASE_LABELS = {
    "alpha": "a",
    "a": "a",
    "beta": "b",
    "b": "b",
    "rc": "rc",
    "pre": "rc",
}


@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: str | None = None
    build: str | None = None


def parse_semver(version: str) -> SemVer:
    """Parse a SemVer 2.0.0 string into its components.

    Raises ValueError if the string does not match the SemVer grammar.
    """
    match = _SEMVER_RE.match(version.strip())
    if match is None:
        raise ValueError(f"not a valid semantic version: {version!r}")

    return SemVer(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        prerelease=match.group("prerelease"),
        build=match.group("build"),
    )


def format_semver(version: SemVer) -> str:
    """Render a SemVer back into its canonical string form."""
    text = f"{version.major}.{version.minor}.{version.patch}"
    if version.prerelease:
        text += f"-{version.prerelease}"
    if version.build:
        text += f"+{version.build}"
    return text


def semver_to_pep440(version: str) -> str:
    """Convert a SemVer 2.0.0 string to a PEP 440 version string.

    Only the first two dot-separated prerelease identifiers are used
    (e.g. "alpha.1" or "rc.2"); anything past that is dropped, since PEP 440
    has no room for an arbitrary-length prerelease chain. Build metadata is
    carried over as a PEP 440 local version segment.
    """
    parsed = parse_semver(version)

    core = f"{parsed.major}.{parsed.minor}.{parsed.patch}"
    pre = _prerelease_to_pep440(parsed.prerelease) if parsed.prerelease else ""
    local = f"+{_sanitize_local(parsed.build)}" if parsed.build else ""

    return core + pre + local


def _prerelease_to_pep440(prerelease: str) -> str:
    parts = prerelease.split(".")
    label = parts[0].lower()

    try:
        pep440_letter = _PRERELEASE_LABELS[label]
    except KeyError:
        raise ValueError(
            f"unsupported prerelease label for PEP 440 conversion: {parts[0]!r}"
        ) from None

    number = parts[1] if len(parts) > 1 and parts[1].isdigit() else "0"
    return f"{pep440_letter}{number}"


def _sanitize_local(build: str) -> str:
    sanitized = _LOCAL_SEGMENT_RE.sub(".", build)
    return sanitized.strip(".")
