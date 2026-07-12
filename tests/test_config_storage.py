from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "modeskill" / "shared" / "scripts"))

from config_storage import config_filename, load_config, save_config


class ConfigStorageTest(unittest.TestCase):
    def test_atomic_local_save_load_and_safe_filename(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = save_config(root, "modelab-workspace", {"ok": True})
            self.assertEqual(load_config(root, "modelab-workspace"), {"ok": True})
            self.assertFalse(any(path.parent.glob(".modeskill-*.tmp")))
        for name in ("../escape", "a/b", "", "..", None):
            with self.assertRaises(ValueError):
                config_filename(name)

    def test_local_and_workspaces_symlink_escapes_are_rejected_before_write(self):
        for escaped in (".local", "workspaces"):
            with self.subTest(escaped=escaped), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                root = base / "repository"
                root.mkdir()
                outside = base / "outside"
                outside.mkdir()
                if escaped == ".local":
                    (root / ".local").symlink_to(outside, target_is_directory=True)
                else:
                    (root / ".local").mkdir()
                    (root / ".local" / "workspaces").symlink_to(outside, target_is_directory=True)
                with self.assertRaises(ValueError):
                    save_config(root, "workspace", {"ok": True})
                self.assertEqual(list(outside.iterdir()), [])

    def test_existing_configuration_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "repository"
            workspaces = root / ".local" / "workspaces"
            workspaces.mkdir(parents=True)
            outside = base / "outside.json"
            outside.write_text('{"unchanged": true}', encoding="utf-8")
            (workspaces / "workspace.json").symlink_to(outside)
            with self.assertRaises(ValueError):
                save_config(root, "workspace", {"changed": True})
            self.assertEqual(json.loads(outside.read_text(encoding="utf-8")), {"unchanged": True})
            with self.assertRaises(ValueError):
                load_config(root, "workspace")


if __name__ == "__main__":
    unittest.main()
