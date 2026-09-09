import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from semverconv.cli import main


class CliTests(unittest.TestCase):
    def _run(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            status = main(list(args))
        return status, out.getvalue().strip(), err.getvalue().strip()

    def test_to_pep440(self):
        status, out, err = self._run("to-pep440", "1.2.3-alpha.1")
        self.assertEqual(status, 0)
        self.assertEqual(out, "1.2.3a1")
        self.assertEqual(err, "")

    def test_to_semver(self):
        status, out, err = self._run("to-semver", "1.2.3a1")
        self.assertEqual(status, 0)
        self.assertEqual(out, "1.2.3-alpha.1")

    def test_invalid_input_prints_error_and_returns_nonzero(self):
        status, out, err = self._run("to-pep440", "not-a-version")
        self.assertEqual(status, 1)
        self.assertEqual(out, "")
        self.assertIn("not a valid semantic version", err)

    def test_missing_command_raises_systemexit(self):
        with self.assertRaises(SystemExit):
            main([])


if __name__ == "__main__":
    unittest.main()
