import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from semverconv import (
    SemVer,
    parse_semver,
    format_semver,
    semver_to_pep440,
    pep440_to_semver,
)


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

    def test_dev_prerelease_becomes_dev_release(self):
        self.assertEqual(semver_to_pep440("1.2.3-dev.1"), "1.2.3.dev1")

    def test_dev_prerelease_without_number(self):
        self.assertEqual(semver_to_pep440("1.2.3-dev"), "1.2.3.dev0")

    def test_post_prerelease_becomes_post_release(self):
        self.assertEqual(semver_to_pep440("1.2.3-post.1"), "1.2.3.post1")


class Pep440ToSemverTests(unittest.TestCase):
    def test_plain_release(self):
        self.assertEqual(pep440_to_semver("1.2.3"), "1.2.3")

    def test_pads_missing_release_parts(self):
        self.assertEqual(pep440_to_semver("1.2"), "1.2.0")
        self.assertEqual(pep440_to_semver("1"), "1.0.0")

    def test_alpha_prerelease(self):
        self.assertEqual(pep440_to_semver("1.2.3a1"), "1.2.3-alpha.1")

    def test_prerelease_without_number(self):
        self.assertEqual(pep440_to_semver("1.2.3b"), "1.2.3-beta.0")

    def test_rc_prerelease(self):
        self.assertEqual(pep440_to_semver("1.2.3rc2"), "1.2.3-rc.2")

    def test_c_label_maps_to_rc(self):
        self.assertEqual(pep440_to_semver("1.2.3c1"), "1.2.3-rc.1")

    def test_local_version_becomes_build_metadata(self):
        self.assertEqual(
            pep440_to_semver("1.2.3+build.5114f85"), "1.2.3+build.5114f85"
        )

    def test_post_release_becomes_post_prerelease(self):
        self.assertEqual(pep440_to_semver("1.2.3.post1"), "1.2.3-post.1")

    def test_dev_release_becomes_dev_prerelease(self):
        self.assertEqual(pep440_to_semver("1.2.3.dev1"), "1.2.3-dev.1")

    def test_round_trip_through_semver_to_pep440(self):
        for text in (
            "1.2.3",
            "1.2.3-alpha.1",
            "1.2.3-rc.2",
            "1.2.3+build.5",
            "1.2.3-dev.1",
            "1.2.3-post.1",
        ):
            self.assertEqual(pep440_to_semver(semver_to_pep440(text)), text)

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            pep440_to_semver("not-a-version")

    def test_rejects_combined_pre_and_post(self):
        with self.assertRaises(ValueError):
            pep440_to_semver("1.2.3a1.post1")

    def test_rejects_combined_pre_and_dev(self):
        with self.assertRaises(ValueError):
            pep440_to_semver("1.2.3a1.dev1")

    def test_rejects_epoch(self):
        with self.assertRaises(ValueError):
            pep440_to_semver("1!1.2.3")


if __name__ == "__main__":
    unittest.main()
