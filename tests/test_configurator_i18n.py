from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGURATOR = ROOT / ".agents" / "skills" / "modeskill" / "configurator"


class HelpButtonParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.help_buttons = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "button" and "help-button" in attributes.get("class", "").split():
            self.help_buttons.append(attributes)


class ConfiguratorI18nTest(unittest.TestCase):
    def test_default_switch_storage_and_fallback_contracts_exist(self):
        app = (CONFIGURATOR / "app.js").read_text(encoding="utf-8")
        self.assertIn('return supportedLanguages.includes(value) ? value : "zh-CN"', app)
        self.assertIn('localStorage.getItem("modeskill-language")', app)
        self.assertIn('localStorage.setItem("modeskill-language", language)', app)
        self.assertIn('addEventListener("change"', app)
        self.assertIn("applyLanguage(event.target.value)", app)

    def test_all_interface_labels_use_central_dictionary(self):
        html = (CONFIGURATOR / "index.html").read_text(encoding="utf-8")
        dictionary = (CONFIGURATOR / "i18n.js").read_text(encoding="utf-8")
        keys = re.findall(r'data-i18n(?:-placeholder)?="([^"]+)"', html)
        self.assertGreater(len(keys), 25)
        for key in keys:
            self.assertGreaterEqual(dictionary.count(f"{key}:"), 2, key)
        self.assertIn('"zh-CN"', dictionary)
        self.assertIn("en:", dictionary)

    def test_distribution_manifest_contains_only_synced_modules(self):
        manifest = json.loads((ROOT / ".agents" / "skills" / "modeskill" / "modules.json").read_text(encoding="utf-8"))
        self.assertEqual([item["id"] for item in manifest["modules"]], ["ui-consistency"])
        self.assertTrue(all(item["distribution"] == "git-synced" for item in manifest["modules"]))

    def test_project_sources_errors_and_help_are_bilingual(self):
        dictionary = (CONFIGURATOR / "i18n.js").read_text(encoding="utf-8")
        app = (CONFIGURATOR / "app.js").read_text(encoding="utf-8")
        for key in ("projectSource", "automatic", "manual", "invalid_host", "invalid_origin", "json_required", "unsafe_path", "helpTerms", "explicitAuthorization"):
            self.assertGreaterEqual(dictionary.count(key), 2, key)
        self.assertIn('t(`projectSource.${project.source}`)', app)
        self.assertNotIn("result.detail", app)
        self.assertIn("result?.error?.code", app)

    def test_help_buttons_have_keyboard_and_accessibility_contract(self):
        parser = HelpButtonParser()
        parser.feed((CONFIGURATOR / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(len(parser.help_buttons), 8)
        for button in parser.help_buttons:
            self.assertEqual(button.get("type"), "button")
            self.assertTrue(button.get("data-help-key"))
            self.assertEqual(button.get("aria-expanded"), "false")
        app = (CONFIGURATOR / "app.js").read_text(encoding="utf-8")
        for key in ('event.key === "Enter"', 'event.key === " "', 'event.key === "Escape"', 'setAttribute("aria-label"', 'tooltip.role = "tooltip"'):
            self.assertIn(key, app)


if __name__ == "__main__":
    unittest.main()
