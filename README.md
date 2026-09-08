# semverconv

A tool that publishes a library under SemVer (say, because it started life as
an npm package, or the project's canonical version lives in a `VERSION` file
shared across languages) still needs a version string Python's packaging
tools will accept when it cuts a wheel. SemVer and PEP 440 look similar but
aren't compatible: `1.2.3-alpha.1` is valid SemVer and invalid PEP 440;
`pip` and `setuptools` want `1.2.3a1` instead.

`semverconv` converts SemVer 2.0.0 strings into PEP 440 strings, and back.

## Usage

```python
from semverconv import semver_to_pep440

semver_to_pep440("1.2.3")                    # "1.2.3"
semver_to_pep440("1.2.3-alpha.1")             # "1.2.3a1"
semver_to_pep440("1.2.3-rc.2")                # "1.2.3rc2"
semver_to_pep440("1.2.3+build.5114f85")       # "1.2.3+build.5114f85"
```

SemVer has no native idea of a post- or dev-release, so `semver_to_pep440`
uses a convention for them: a prerelease whose first identifier is `dev` or
`post` becomes a PEP 440 dev- or post-release segment instead of a lettered
prerelease.

```python
semver_to_pep440("1.2.3-dev.1")               # "1.2.3.dev1"
semver_to_pep440("1.2.3-post.2")              # "1.2.3.post2"
```

`pep440_to_semver` goes the other way, for the subset of PEP 440 that
`semver_to_pep440` can produce:

```python
from semverconv import pep440_to_semver

pep440_to_semver("1.2.3")                     # "1.2.3"
pep440_to_semver("1.2.3a1")                   # "1.2.3-alpha.1"
pep440_to_semver("1.2.3rc2")                  # "1.2.3-rc.2"
pep440_to_semver("1.2.3+build.5114f85")       # "1.2.3+build.5114f85"
pep440_to_semver("1.2.3.dev1")                # "1.2.3-dev.1"
pep440_to_semver("1.2.3.post2")               # "1.2.3-post.2"
```

Parsing and formatting are also exposed on their own, for when you just need
to pick apart a version string:

```python
from semverconv import parse_semver, format_semver

v = parse_semver("2.1.0-beta.3+exp.sha.5114f85")
v.major, v.minor, v.patch   # 2, 1, 0
v.prerelease                # "beta.3"
v.build                     # "exp.sha.5114f85"

format_semver(v)             # "2.1.0-beta.3+exp.sha.5114f85"
```

A SemVer prerelease chain longer than a label and a number has no PEP 440
prerelease equivalent, so the full chain is carried in the local version
instead:

```python
semver_to_pep440("1.2.3-alpha.1.2")           # "1.2.3a1+sv3.alpha.1.2"
pep440_to_semver("1.2.3a1+sv3.alpha.1.2")     # "1.2.3-alpha.1.2"
```

The `svN.` prefix records how many identifiers to read back off the local
version, so build metadata can still follow it in the same local version
(`1.2.3-alpha.1.2+build.5` becomes `1.2.3a1+sv3.alpha.1.2.build.5`).

Every function is pure: given the same string, it always returns the same
result, and none of them touch the filesystem, environment, or network. That
also means they compose cleanly with anything that needs a version string —
a `setup.py`, a release script, a CI step.

## Known limitations (first pass)

- Only `alpha`, `beta`, and `rc` prerelease labels convert; anything else
  raises `ValueError`. There's no PEP 440 equivalent for an arbitrary label
  like `nightly`, so this needs a documented convention before it's handled.
- A prerelease identifier containing a hyphen (e.g. `alpha.some-id`) can't
  be smuggled through a PEP 440 local version losslessly, since PEP 440's
  local version alphabet has no hyphen. `semver_to_pep440` raises
  `ValueError` rather than corrupt it.
- Build metadata that happens to start with something matching the `svN.`
  chain marker (e.g. `+sv2.foo.bar` as literal build metadata, not a
  smuggled chain) will be misread by `pep440_to_semver` as a prerelease
  chain. This is an inherent risk of using the local version as a carrier.
- `pep440_to_semver` only understands a bare release segment plus at most
  one of an `a`/`b`/`rc` prerelease, a `.postN`, or a `.devN` release, plus
  a local version. PEP 440 epochs, and versions that combine a prerelease
  with a post- or dev-release (e.g. `1.2.3a1.dev1`), raise `ValueError` —
  SemVer only has one prerelease chain, so there's no way to represent both
  at once.

## Running the tests

```
python -m unittest discover tests
```

## License

MIT, see [LICENSE](LICENSE).
