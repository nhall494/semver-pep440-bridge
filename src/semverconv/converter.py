"""Convert between Semantic Versioning 2.0.0 and PEP 440 version strings.

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

# Mirrors _PRERELEASE_LABELS in the other direction. PEP 440 accepts a few
# spellings ("c", "pre", "preview") that SemVer has no equivalent for, so
# they all collapse onto the closest SemVer label.
_PEP440_PRERELEASE_LABELS = {
    "a": "alpha",
    "alpha": "alpha",
    "b": "beta",
    "beta": "beta",
    "rc": "rc",
    "c": "rc",
    "pre": "rc",
    "preview": "rc",
}

# Subset of the PEP 440 grammar this module can round-trip back to SemVer:
# a bare release segment of one to three numbers, then at most one of a
# prerelease, a post-release, or a dev-release (this module's SemVer model
# can't express two of those at once, since SemVer only has room for a
# single prerelease chain), and an optional local version. Epochs, and
# combinations of pre/post/dev, have no SemVer equivalent and are rejected.
_PEP440_RE = re.compile(
    r"^(?P<release>\d+(?:\.\d+){0,2})"
    r"(?:(?P<pre_label>a|b|c|rc|alpha|beta|pre|preview)(?P<pre_number>\d*)"
    r"|\.post(?P<post_number>\d+)"
    r"|\.dev(?P<dev_number>\d+))?"
    r"(?:\+(?P<local>[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*))?$"
)


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

    SemVer has no native concept of post- or dev-releases, so this module
    uses a convention: a prerelease whose first identifier is "dev" or
    "post" (e.g. "1.2.3-dev.1" or "1.2.3-post.2") becomes a PEP 440 dev- or
    post-release segment instead of a lettered prerelease. Since SemVer only
    has one prerelease chain, a version can't carry both a prerelease and a
    post/dev segment at once.
    """
    parsed = parse_semver(version)

    core = f"{parsed.major}.{parsed.minor}.{parsed.patch}"
    pre = _prerelease_to_pep440(parsed.prerelease) if parsed.prerelease else ""
    local = f"+{_sanitize_local(parsed.build)}" if parsed.build else ""

    return core + pre + local


def _prerelease_to_pep440(prerelease: str) -> str:
    parts = prerelease.split(".")
    label = parts[0].lower()
    number = parts[1] if len(parts) > 1 and parts[1].isdigit() else "0"

    if label == "dev":
        return f".dev{number}"
    if label == "post":
        return f".post{number}"

    try:
        pep440_letter = _PRERELEASE_LABELS[label]
    except KeyError:
        raise ValueError(
            f"unsupported prerelease label for PEP 440 conversion: {parts[0]!r}"
        ) from None

    return f"{pep440_letter}{number}"


def _sanitize_local(build: str) -> str:
    sanitized = _LOCAL_SEGMENT_RE.sub(".", build)
    return sanitized.strip(".")


def pep440_to_semver(version: str) -> str:
    """Convert a PEP 440 version string back to a SemVer 2.0.0 string.

    Handles the subset of PEP 440 that semver_to_pep440 can produce: a
    release segment of up to three numbers (missing trailing numbers are
    treated as 0, matching PEP 440's own rule), at most one of an a/b/rc
    prerelease, a post-release, or a dev-release, and an optional local
    version (carried straight over as SemVer build metadata, since PEP 440's
    local version alphabet is already valid there). A post- or dev-release
    becomes a SemVer prerelease whose first identifier is "post" or "dev"
    (see semver_to_pep440's docstring for the convention this mirrors).
    Epochs, and versions combining pre/post/dev, have no SemVer equivalent
    and raise ValueError.
    """
    match = _PEP440_RE.match(version.strip())
    if match is None:
        raise ValueError(
            f"not a PEP 440 version this module can convert to SemVer: {version!r}"
        )

    release = [int(part) for part in match.group("release").split(".")]
    release += [0] * (3 - len(release))
    major, minor, patch = release

    prerelease = None
    pre_label = match.group("pre_label")
    post_number = match.group("post_number")
    dev_number = match.group("dev_number")
    if pre_label is not None:
        semver_label = _PEP440_PRERELEASE_LABELS[pre_label.lower()]
        number = int(match.group("pre_number") or "0")
        prerelease = f"{semver_label}.{number}"
    elif post_number is not None:
        prerelease = f"post.{int(post_number)}"
    elif dev_number is not None:
        prerelease = f"dev.{int(dev_number)}"

    build = match.group("local")

    return format_semver(SemVer(major, minor, patch, prerelease, build))
