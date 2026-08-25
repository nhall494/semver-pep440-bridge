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

`pep440_to_semver` goes the other way, for the subset of PEP 440 that
`semver_to_pep440` can produce:

```python
from semverconv import pep440_to_semver

pep440_to_semver("1.2.3")                     # "1.2.3"
pep440_to_semver("1.2.3a1")                   # "1.2.3-alpha.1"
pep440_to_semver("1.2.3rc2")                  # "1.2.3-rc.2"
pep440_to_semver("1.2.3+build.5114f85")       # "1.2.3+build.5114f85"
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

Every function is pure: given the same string, it always returns the same
result, and none of them touch the filesystem, environment, or network. That
also means they compose cleanly with anything that needs a version string —
a `setup.py`, a release script, a CI step.

## Known limitations (first pass)

- Only `alpha`, `beta`, and `rc` prerelease labels convert; anything else
  raises `ValueError`. There's no PEP 440 equivalent for an arbitrary label
  like `nightly`, so this needs a documented convention before it's handled.
- Only the first two prerelease identifiers are used (`alpha.1.2` becomes
  `a1`, dropping the trailing `.2`). PEP 440 prereleases don't support a
  chain of identifiers the way SemVer does.
- `pep440_to_semver` only understands a bare release segment plus an
  optional `a`/`b`/`rc` prerelease and local version. PEP 440 epochs,
  `.postN`, and `.devN` releases raise `ValueError` — there's no SemVer
  equivalent for them wired up yet.

## Running the tests

```
python -m unittest discover tests
```

## License

MIT, see [LICENSE](LICENSE).
