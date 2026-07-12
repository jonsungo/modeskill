from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryIntegrityTest(unittest.TestCase):
    def test_repository_validator_passes(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_modeskill.py")], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_examples_contain_accessible_interactions(self):
        for project in ("reference-project", "target-project"):
            html = (ROOT / "examples" / project / "index.html").read_text(encoding="utf-8")
            script = (ROOT / "examples" / project / "app.js").read_text(encoding="utf-8")
            for token in ("required", "aria-describedby", "role=\"dialog\"", "aria-modal=\"true\"", "disabled"):
                self.assertIn(token, html)
            for token in ("Escape", "event.target === overlay", "returnFocus.focus"):
                self.assertIn(token, script)


if __name__ == "__main__":
    unittest.main()
