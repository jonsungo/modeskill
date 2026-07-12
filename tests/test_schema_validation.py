from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "modeskill"
ASSETS = SKILL / "ui-consistency" / "assets"


class SchemaValidationTest(unittest.TestCase):
    def run_script(self, relative: str, *args: str):
        return subprocess.run([sys.executable, str(SKILL / relative), *args], cwd=ROOT, text=True, capture_output=True, check=False)

    def test_all_examples_validate(self):
        self.assertEqual(self.run_script("shared/scripts/validate_config.py").returncode, 0)
        self.assertEqual(self.run_script("ui-consistency/scripts/validate_profile.py").returncode, 0)
        self.assertEqual(self.run_script("ui-consistency/scripts/validate_report.py").returncode, 0)

    def test_report_summary_mismatch_fails(self):
        data = json.loads((ASSETS / "consistency-report.example.json").read_text(encoding="utf-8"))
        data["summary"]["inherited"] = 9
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "report.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = self.run_script("ui-consistency/scripts/validate_report.py", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("summary inherited=9", result.stderr)

    def test_duplicate_dimensions_fail(self):
        data = json.loads((ASSETS / "workspace.example.json").read_text(encoding="utf-8"))
        data["analysis"]["dimensions"].append("typography")
        schema_path = SKILL / "shared" / "schemas" / "workspace.schema.json"
        sys.path.insert(0, str(SKILL / "shared" / "scripts"))
        from schema_utils import SchemaError, validate_document
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        with self.assertRaises(SchemaError):
            validate_document(schema, data)

    def test_forged_discovery_cache_id_fails(self):
        data = json.loads((ASSETS / "workspace.example.json").read_text(encoding="utf-8"))
        data["discovery_cache"]["discovered_projects"][0]["id"] = "forged"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "workspace.json"
            data["workspace"]["root"] = str(ROOT / "examples")
            path.write_text(json.dumps(data), encoding="utf-8")
            result = self.run_script("shared/scripts/validate_config.py", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("id/path must equal normalized relative path", result.stderr)


if __name__ == "__main__":
    unittest.main()
