import json
import tempfile
import unittest
from pathlib import Path

from automation import autonomy_engine


class TestAutonomyEngine(unittest.TestCase):
    def test_worst_case_matrix(self):
        matrix = autonomy_engine.evaluate_worst_case()
        self.assertIn("ci_failure", matrix)
        self.assertIn("tampered_ciphertext", matrix)

    def test_report_generation(self):
        with tempfile.TemporaryDirectory() as d:
            report = Path(d) / "report.json"
            # emulate CLI invocation by temporarily overriding argv
            import sys
            old = sys.argv
            sys.argv = ["autonomy_engine.py", "--report", str(report), "--quick"]
            try:
                rc = autonomy_engine.main()
            finally:
                sys.argv = old
            self.assertIn(rc, (0, 1))
            data = json.loads(report.read_text())
            self.assertIn("status", data)
            self.assertIn("checks", data)


if __name__ == "__main__":
    unittest.main()
