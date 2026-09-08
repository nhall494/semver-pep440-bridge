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

    A prerelease made of just a label and a number (e.g. "alpha.1" or "rc")
    maps onto PEP 440's own prerelease segment directly. A longer chain, or
    one whose second identifier isn't a number (e.g. "alpha.1.2" or
    "rc.candidate"), has no PEP 440 prerelease equivalent, so the full
    original chain is stashed verbatim in the PEP 440 local version instead
    (see _prerelease_to_pep440), letting pep440_to_semver recover it
    exactly. Build metadata is also carried over as a local version segment,
    appended after the chain if both are present.

    SemVer has no native concept of post- or dev-releases, so this module
    uses a convention: a prerelease whose first identifier is "dev" or
    "post" (e.g. "1.2.3-dev.1" or "1.2.3-post.2") becomes a PEP 440 dev- or
    post-release segment instead of a lettered prerelease. Since SemVer only
    has one prerelease chain, a version can't carry both a prerelease and a
    post/dev segment at once.
    """
    parsed = parse_semver(version)

    core = f"{parsed.major}.{parsed.minor}.{parsed.patch}"
    if parsed.prerelease:
        pre, chain_local = _prerelease_to_pep440(parsed.prerelease)
    else:
        pre, chain_local = "", ""
    build_local = _sanitize_local(parsed.build) if parsed.build else ""

    local_segments = [segment for segment in (chain_local, build_local) if segment]
    local = f"+{'.'.join(local_segments)}" if local_segments else ""

    return core + pre + local


def _prerelease_to_pep440(prerelease: str) -> tuple[str, str]:
    """Return (pep440 prerelease segment, local version chain segment).

    The second element is "" when the label and number alone reconstruct
    the original prerelease exactly. Otherwise it's an "svN.<identifiers>"
    segment (N = identifier count) that records the full original chain so
    pep440_to_semver can rebuild it losslessly instead of silently losing
    everything past the second identifier.
    """
    parts = prerelease.split(".")
    label = parts[0].lower()
    number = parts[1] if len(parts) > 1 and parts[1].isdigit() else "0"

    if label == "dev":
        segment = f".dev{number}"
    elif label == "post":
        segment = f".post{number}"
    else:
        try:
            pep440_letter = _PRERELEASE_LABELS[label]
        except KeyError:
            raise ValueError(
                f"unsupported prerelease label for PEP 440 conversion: {parts[0]!r}"
            ) from None
        segment = f"{pep440_letter}{number}"

    reconstructed = [label, number] if len(parts) > 1 else [label]
    if parts == reconstructed:
        return segment, ""

    for part in parts:
        if not part.isalnum():
            raise ValueError(
                "prerelease identifiers containing '-' can't be losslessly "
                f"represented in a PEP 440 local version: {prerelease!r}"
            )

    return segment, f"sv{len(parts)}." + ".".join(parts)


def _sanitize_local(build: str) -> str:
    sanitized = _LOCAL_SEGMENT_RE.sub(".", build)
    return sanitized.strip(".")


# Matches the "svN" marker _prerelease_to_pep440 writes at the start of a
# local version to smuggle a full prerelease chain through PEP 440.
_CHAIN_LOCAL_RE = re.compile(r"^sv(\d+)$")


def _extract_prerelease_chain(local: str) -> tuple[str, str | None] | None:
    """Recover a SemVer prerelease chain smuggled into a PEP 440 local
    version by _prerelease_to_pep440. Returns None if `local` doesn't start
    with an "svN." marker, leaving it to be treated as plain build metadata.
    """
    segments = local.split(".")
    marker = _CHAIN_LOCAL_RE.match(segments[0])
    if marker is None:
        return None

    count = int(marker.group(1))
    chain, remainder = segments[1 : 1 + count], segments[1 + count :]
    if len(chain) != count:
        raise ValueError(f"malformed prerelease chain in local version: {local!r}")

    return ".".join(chain), ".".join(remainder) if remainder else None


def pep440_to_semver(version: str) -> str:
    """Convert a PEP 440 version string back to a SemVer 2.0.0 string.

    Handles the subset of PEP 440 that semver_to_pep440 can produce: a
    release segment of up to three numbers (missing trailing numbers are
    treated as 0, matching PEP 440's own rule), at most one of an a/b/rc
    prerelease, a post-release, or a dev-release, and an optional local
    version. A post- or dev-release becomes a SemVer prerelease whose first
    identifier is "post" or "dev" (see semver_to_pep440's docstring for the
    convention this mirrors). If the local version starts with the "svN."
    marker semver_to_pep440 writes for a multi-identifier prerelease chain,
    that chain is restored verbatim and anything left over in the local
    version after it is treated as SemVer build metadata; otherwise the
    whole local version is carried straight over as build metadata, since
    PEP 440's local version alphabet is already valid there. Epochs, and
    versions combining pre/post/dev, have no SemVer equivalent and raise
    ValueError.
    """
    match = _PEP440_RE.match(version.strip())
    if match is None:
        raise ValueError(
            f"not a PEP 440 version this module can convert to SemVer: {version!r}"
        )

    release = [int(part) for part in match.group("release").split(".")]
    release += [0] * (3 - len(release))
    major, minor, patch = release

    build = match.group("local")
    chain = _extract_prerelease_chain(build) if build else None

    if chain is not None:
        prerelease, build = chain
    else:
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

    return format_semver(SemVer(major, minor, patch, prerelease, build))
