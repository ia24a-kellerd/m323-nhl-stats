"""Bridge for unittest runners (e.g. PyCharm's default): runs the whole pytest suite as one test.

The file name does not match pytest's test_*.py pattern, so pytest itself does not collect it.
"""

import subprocess
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent


class PytestSuite(unittest.TestCase):
    def test_all_pytest_tests_pass(self):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(TESTS_DIR), "-v", "--color=no"],
            cwd=TESTS_DIR.parent,
            capture_output=True,
            text=True,
        )
        print(result.stdout, result.stderr)
        self.assertEqual(result.returncode, 0, "some pytest tests failed, see output above")
