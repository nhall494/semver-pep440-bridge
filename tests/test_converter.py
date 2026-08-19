import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from semverconv import SemVer, parse_semver, format_semver, semver_to_pep440


class ParseSemverTests(unittest.TestCase):
    def test_basic_version(self):
        self.assertEqual(parse_semver("1.2.3"), SemVer(1, 2, 3))

    def test_prerelease_and_build(self):
        parsed = parse_semver("2.0.0-alpha.1+build.5")
        self.assertEqual(parsed.prerelease, "alpha.1")
        self.assertEqual(parsed.build, "build.5")

    def test_rejects_leading_zero(self):
        with self.assertRaises(ValueError):
            parse_semver("01.2.3")

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            parse_semver("not-a-version")


class FormatSemverTests(unittest.TestCase):
    def test_round_trip(self):
        text = "1.2.3-rc.1+exp.sha.5114f85"
        self.assertEqual(format_semver(parse_semver(text)), text)

    def test_omits_absent_parts(self):
        self.assertEqual(format_semver(SemVer(1, 0, 0)), "1.0.0")


class SemverToPep440Tests(unittest.TestCase):
    def test_plain_release(self):
        self.assertEqual(semver_to_pep440("1.2.3"), "1.2.3")

    def test_alpha_prerelease(self):
        self.assertEqual(semver_to_pep440("1.2.3-alpha.1"), "1.2.3a1")

    def test_beta_prerelease_without_number(self):
        self.assertEqual(semver_to_pep440("1.2.3-beta"), "1.2.3b0")

    def test_rc_prerelease(self):
        self.assertEqual(semver_to_pep440("1.2.3-rc.2"), "1.2.3rc2")

    def test_build_metadata_becomes_local_version(self):
        self.assertEqual(
            semver_to_pep440("1.2.3+build.5114f85"), "1.2.3+build.5114f85"
        )

    def test_build_metadata_with_hyphens_is_sanitized(self):
        self.assertEqual(semver_to_pep440("1.2.3+exp-sha-5114f85"), "1.2.3+exp.sha.5114f85")

    def test_unsupported_prerelease_label_raises(self):
        with self.assertRaises(ValueError):
            semver_to_pep440("1.2.3-nightly.1")


if __name__ == "__main__":
    unittest.main()
