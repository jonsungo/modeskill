from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "modeskill" / "shared" / "scripts"))

from path_security import PathSecurityError, check_project_access, resolve_inside


class AuthorizationTest(unittest.TestCase):
    def test_resolved_path_boundaries_and_roles(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            workspace = base / "workspace"
            target = workspace / "target"
            reference = workspace / "easy"
            target.mkdir(parents=True)
            reference.mkdir()
            outside = base / "outside"
            outside.mkdir()
            (workspace / "escape").symlink_to(outside, target_is_directory=True)

            self.assertEqual(resolve_inside(workspace, "target"), target.resolve())
            self.assertEqual(resolve_inside(workspace, target.resolve()), target.resolve())
            with self.assertRaises(PathSecurityError):
                resolve_inside(workspace, outside)
            with self.assertRaises(PathSecurityError):
                resolve_inside(workspace, "../outside")
            with self.assertRaises(PathSecurityError):
                resolve_inside(workspace, "escape")

            self.assertFalse(check_project_access(reference, role="primary-reference", operation="write", target_write_policy="explicit-per-task", current_task_authorized=True)[0])
            self.assertFalse(check_project_access(target, role="target", operation="write", target_write_policy="explicit-per-task", current_task_authorized=False)[0])
            self.assertTrue(check_project_access(target, role="target", operation="write", target_write_policy="explicit-per-task", current_task_authorized=True)[0])
            self.assertFalse(check_project_access(target, role="target", operation="write", target_write_policy="explicit-per-task", current_task_authorized=True, requested_path=reference / "file.css")[0])
            self.assertFalse(check_project_access(reference, role="other", operation="write", target_write_policy="explicit-per-task", current_task_authorized=True)[0])


if __name__ == "__main__":
    unittest.main()
