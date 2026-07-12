from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "skills" / "modeskill" / "shared" / "scripts"
MODULE_SCRIPT = SCRIPTS / "module_registry.py"
sys.path.insert(0, str(SCRIPTS))

from module_registry import DISABLED_MESSAGE, INVALID_MESSAGE, ModuleRegistryError, UNAVAILABLE_MESSAGE, find_repository_root, load_local_modules, set_local_module_enabled, validate_module_id


class ModuleRegistryTest(unittest.TestCase):
    def make_repository(self, base: Path) -> tuple[Path, Path]:
        root = base / "repository"
        skill = root / ".agents" / "skills" / "modeskill"
        module = root / ".local" / "modules" / "local-helper"
        skill.mkdir(parents=True)
        module.mkdir(parents=True)
        (root / "AGENTS.md").write_text("rules", encoding="utf-8")
        (root / "README.md").write_text("readme", encoding="utf-8")
        (skill / "SKILL.md").write_text("---\nname: modeskill\n---", encoding="utf-8")
        (module / "instructions.md").write_text("generic local instructions", encoding="utf-8")
        self.write_module(module)
        self.write_registry(root)
        return root, skill

    def write_module(self, module: Path, **overrides) -> None:
        data = {
            "id": "local-helper", "distribution": "local-only", "enabled": True,
            "entry_references": ["instructions.md"],
            "display_name": {"zh-CN": "本机助手", "en": "Local helper"},
            "description": {"zh-CN": "临时测试模块", "en": "Temporary test module"}
        }
        data.update(overrides)
        (module / "module.json").write_text(json.dumps(data), encoding="utf-8")

    def write_registry(self, root: Path, *, enabled=True, path="local-helper") -> Path:
        registry = root / ".local" / "modules" / "registry.json"
        registry.write_text(json.dumps({"schemaVersion": "0.1", "modules": [{"id": "local-helper", "path": path, "enabled": enabled}]}), encoding="utf-8")
        return registry

    def test_loads_from_repository_and_skill_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root, skill = self.make_repository(base)
            self.assertEqual(find_repository_root(skill / "SKILL.md"), root.resolve())
            link = base / "linked-skill"
            link.symlink_to(skill, target_is_directory=True)
            self.assertEqual(find_repository_root(link / "SKILL.md"), root.resolve())
            loaded = load_local_modules(root)[0]
            self.assertEqual(loaded["id"], "local-helper")
            self.assertTrue(Path(loaded["entry_references"][0]).is_file())

    def test_missing_repository_returns_required_message(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "SKILL.md"
            path.write_text("no repository", encoding="utf-8")
            with self.assertRaisesRegex(ModuleRegistryError, UNAVAILABLE_MESSAGE):
                find_repository_root(path)

    def test_registry_and_module_file_symlink_escapes_are_rejected(self):
        for filename in ("registry.json", "module.json"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                root, _ = self.make_repository(base)
                if filename == "registry.json":
                    target = root / ".local" / "modules" / filename
                    outside_data = {"modules": []}
                else:
                    target = root / ".local" / "modules" / "local-helper" / filename
                    outside_data = {"id": "local-helper", "distribution": "local-only", "enabled": True, "entry_references": ["instructions.md"]}
                outside = base / filename
                outside.write_text(json.dumps(outside_data), encoding="utf-8")
                target.unlink()
                target.symlink_to(outside)
                with self.assertRaises(ModuleRegistryError):
                    load_local_modules(root, require_registry=True)

    def test_entry_reference_traversal_absolute_and_symlink_escape_are_rejected(self):
        for value in ("../outside.md", "/tmp/outside.md", ""):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temp:
                root, _ = self.make_repository(Path(temp))
                module = root / ".local" / "modules" / "local-helper"
                self.write_module(module, entry_references=[value])
                with self.assertRaises(ModuleRegistryError):
                    load_local_modules(root)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root, _ = self.make_repository(base)
            module = root / ".local" / "modules" / "local-helper"
            outside = base / "outside.md"
            outside.write_text("outside", encoding="utf-8")
            (module / "escape.md").symlink_to(outside)
            self.write_module(module, entry_references=["escape.md"])
            with self.assertRaises(ModuleRegistryError):
                load_local_modules(root)

    def test_internal_entry_symlink_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            root, _ = self.make_repository(Path(temp))
            module = root / ".local" / "modules" / "local-helper"
            (module / "alias.md").symlink_to(module / "instructions.md")
            self.write_module(module, entry_references=["alias.md"])
            loaded = load_local_modules(root)[0]
            self.assertEqual(Path(loaded["entry_references"][0]), (module / "instructions.md").resolve())

    def test_module_local_and_modules_directory_symlink_escapes_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root, _ = self.make_repository(base)
            module = root / ".local" / "modules" / "local-helper"
            outside = base / "outside-module"
            outside.mkdir()
            for child in module.iterdir():
                child.unlink()
            module.rmdir()
            module.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ModuleRegistryError):
                load_local_modules(root)
        for escaped in (".local", "modules"):
            with self.subTest(escaped=escaped), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                root = base / "repository"
                skill = root / ".agents" / "skills" / "modeskill"
                skill.mkdir(parents=True)
                (root / "AGENTS.md").write_text("rules", encoding="utf-8")
                (root / "README.md").write_text("readme", encoding="utf-8")
                (skill / "SKILL.md").write_text("skill", encoding="utf-8")
                outside = base / "outside"
                outside.mkdir()
                if escaped == ".local":
                    (root / ".local").symlink_to(outside, target_is_directory=True)
                else:
                    (root / ".local").mkdir()
                    (root / ".local" / "modules").symlink_to(outside, target_is_directory=True)
                with self.assertRaises(ModuleRegistryError):
                    load_local_modules(root, require_registry=True)

    def test_registry_and_metadata_types_are_strict(self):
        with tempfile.TemporaryDirectory() as temp:
            root, _ = self.make_repository(Path(temp))
            registry = root / ".local" / "modules" / "registry.json"
            registry.write_text("[]", encoding="utf-8")
            with self.assertRaises(ModuleRegistryError):
                load_local_modules(root)
        with tempfile.TemporaryDirectory() as temp:
            root, _ = self.make_repository(Path(temp))
            registry = root / ".local" / "modules" / "registry.json"
            registry.write_text(json.dumps({"modules": ["not-an-object"]}), encoding="utf-8")
            with self.assertRaises(ModuleRegistryError):
                load_local_modules(root)
        with tempfile.TemporaryDirectory() as temp:
            root, _ = self.make_repository(Path(temp))
            module_json = root / ".local" / "modules" / "local-helper" / "module.json"
            module_json.write_text("[]", encoding="utf-8")
            with self.assertRaises(ModuleRegistryError):
                load_local_modules(root)
        for value in ("false", 0, 1, None, [], {}):
            with self.subTest(enabled=value), tempfile.TemporaryDirectory() as temp:
                root, _ = self.make_repository(Path(temp))
                self.write_registry(root, enabled=value)
                with self.assertRaisesRegex(ModuleRegistryError, INVALID_MESSAGE):
                    load_local_modules(root)
        for value in ("false", 0, None):
            with self.subTest(metadata_enabled=value), tempfile.TemporaryDirectory() as temp:
                root, _ = self.make_repository(Path(temp))
                module = root / ".local" / "modules" / "local-helper"
                self.write_module(module, enabled=value)
                with self.assertRaisesRegex(ModuleRegistryError, INVALID_MESSAGE):
                    load_local_modules(root)
        with tempfile.TemporaryDirectory() as temp:
            root, _ = self.make_repository(Path(temp))
            module = root / ".local" / "modules" / "local-helper"
            self.write_module(module, entry_references="instructions.md")
            with self.assertRaises(ModuleRegistryError):
                load_local_modules(root)

    def test_enablement_missing_module_and_names_are_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            root, skill = self.make_repository(Path(temp))
            set_local_module_enabled(root, "local-helper", False)
            self.assertFalse(load_local_modules(root)[0]["enabled"])
            result = subprocess.run([sys.executable, str(MODULE_SCRIPT), "--skill-path", str(skill / "SKILL.md"), "--module", "local-helper"], text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn(DISABLED_MESSAGE, result.stdout)
            missing = subprocess.run([sys.executable, str(MODULE_SCRIPT), "--skill-path", str(skill / "SKILL.md"), "--module", "missing-helper"], text=True, capture_output=True, check=False)
            self.assertEqual(missing.returncode, 1)
            self.assertIn(UNAVAILABLE_MESSAGE, missing.stdout)
            for value in ("../escape", "a/b", "a\\b", "UPPER", "", None):
                with self.assertRaises(ModuleRegistryError):
                    validate_module_id(value)


if __name__ == "__main__":
    unittest.main()
