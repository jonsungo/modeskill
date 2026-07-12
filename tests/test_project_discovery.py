from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / ".agents" / "skills" / "modeskill" / "shared" / "scripts"
sys.path.insert(0, str(SHARED))

from path_security import PathSecurityError
from project_discovery import DEFAULT_EXCLUDED, DEFAULT_MARKERS, discover_projects


class ProjectDiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.workspace = base / "workspace"
        self.workspace.mkdir()
        (self.workspace / ".git").mkdir()
        for name in ("easy", "trans", "target", "node_modules", "manual-app"):
            (self.workspace / name).mkdir()
        (self.workspace / "easy" / "package.json").write_text("{}", encoding="utf-8")
        (self.workspace / "trans" / "index.html").write_text("<!doctype html>", encoding="utf-8")
        (self.workspace / "trans" / "src").mkdir()
        (self.workspace / "target" / "composer.json").write_text("{}", encoding="utf-8")
        (self.workspace / "node_modules" / "package.json").write_text("{}", encoding="utf-8")
        outside = base / "outside"
        outside.mkdir()
        (outside / "package.json").write_text("{}", encoding="utf-8")
        (self.workspace / "escaping-link").symlink_to(outside, target_is_directory=True)

    def tearDown(self):
        self.temp.cleanup()

    def config(self):
        return {
            "automatic": True, "recursive": True, "max_depth": 4,
            "treat_workspace_root_as_project": False,
            "continue_below_repository_root": True,
            "project_markers": DEFAULT_MARKERS,
            "include_patterns": ["**"], "exclude_patterns": [],
            "excluded_directories": DEFAULT_EXCLUDED,
        }

    def test_repository_root_does_not_stop_child_discovery(self):
        result = discover_projects(self.workspace, self.config(), [])
        paths = {item["path"] for item in result["projects"]}
        self.assertEqual(paths, {"easy", "trans", "target"})
        self.assertNotIn(".", paths)
        self.assertNotIn("node_modules", paths)
        self.assertIn("escaping-link", result["rejected_paths"])

    def test_manual_markerless_project_merges_with_discovery(self):
        result = discover_projects(self.workspace, self.config(), [{"name": "Manual", "path": "manual-app"}, {"name": "Easy manual", "path": "easy"}])
        paths = [item["path"] for item in result["projects"]]
        self.assertIn("manual-app", paths)
        self.assertEqual(paths.count("easy"), 1)

    def test_manual_project_outside_workspace_is_rejected(self):
        with self.assertRaises(PathSecurityError):
            discover_projects(self.workspace, self.config(), [{"name": "Outside", "path": "../outside"}])

    def test_max_depth_is_enforced(self):
        config = self.config()
        config["max_depth"] = 0
        self.assertEqual(discover_projects(self.workspace, config, [])["projects"], [])


if __name__ == "__main__":
    unittest.main()
