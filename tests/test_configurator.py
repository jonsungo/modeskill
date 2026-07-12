from __future__ import annotations

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CONFIGURATOR = ROOT / ".agents" / "skills" / "modeskill" / "configurator"
SERVER_PATH = CONFIGURATOR / "server.py"


class ConfiguratorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("modeskill_configurator", SERVER_PATH)
        cls.server = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.server)

    def test_server_binds_loopback_only(self):
        with patch.object(self.server, "ThreadingHTTPServer") as server_class:
            self.server.create_server(0)
        server_class.assert_called_once_with(("127.0.0.1", 0), self.server.Handler)

    def test_host_and_origin_policy(self):
        for host in ("127.0.0.1", "localhost", "127.0.0.1:8765", "localhost:8765"):
            self.server.validate_host(host, 8765)
        for host in (None, "evil.test", "localhost:9000", "127.0.0.2"):
            with self.assertRaises(self.server.ApiError):
                self.server.validate_host(host, 8765)
        for origin in ("http://127.0.0.1:8765", "http://localhost:8765"):
            self.server.validate_origin(origin, 8765, "127.0.0.1")
        self.server.validate_origin(None, 8765, "127.0.0.1")
        for origin, client in (("https://evil.test", "127.0.0.1"), (None, "192.0.2.1")):
            with self.assertRaises(self.server.ApiError):
                self.server.validate_origin(origin, 8765, client)

    def test_json_content_type_size_and_top_level_types(self):
        valid = json.dumps({"ok": True}).encode("utf-8")
        self.assertEqual(self.server.parse_json_payload("application/json; charset=utf-8", str(len(valid)), io.BytesIO(valid).read), {"ok": True})
        for content_type in (None, "text/plain", "multipart/form-data"):
            with self.assertRaisesRegex(self.server.ApiError, "json_required"):
                self.server.parse_json_payload(content_type, "2", io.BytesIO(b"{}").read)
        with self.assertRaisesRegex(self.server.ApiError, "request_too_large"):
            self.server.parse_json_payload("application/json", str(self.server.MAX_BODY + 1), io.BytesIO(b"").read)
        for value in ([], "text", 1, None, True):
            body = json.dumps(value).encode("utf-8")
            with self.assertRaisesRegex(self.server.ApiError, "json_object_required"):
                self.server.parse_json_payload("application/json", str(len(body)), io.BytesIO(body).read)

    def test_module_enabled_requires_json_boolean(self):
        self.assertEqual(self.server.validate_module_toggle({"module_id": "local-helper", "enabled": True}), ("local-helper", True))
        for value in ("false", "true", 0, 1, None, [], {}):
            with self.subTest(enabled=value), self.assertRaisesRegex(self.server.ApiError, "invalid_module_toggle"):
                self.server.validate_module_toggle({"module_id": "local-helper", "enabled": value})

    def test_unsupported_methods_are_explicit(self):
        for method in ("do_OPTIONS", "do_PUT", "do_PATCH", "do_DELETE"):
            self.assertTrue(hasattr(self.server.Handler, method))
        handler = object.__new__(self.server.Handler)
        captured = []
        handler._validate_host = lambda: None
        handler._send_error = lambda error: captured.append((error.status, error.code))
        handler._method_not_allowed()
        self.assertEqual(captured, [(405, "method_not_allowed")])

    def test_error_response_does_not_expose_stack_or_path(self):
        handler = object.__new__(self.server.Handler)
        captured = []
        handler._json = lambda status, payload: captured.append((status, payload))
        handler._send_error(self.server.PathSecurityError("private path details"))
        self.assertEqual(captured, [(400, {"error": {"code": "unsafe_path"}})])

    def test_interface_has_required_actions_and_no_git_commands(self):
        html = (CONFIGURATOR / "index.html").read_text(encoding="utf-8")
        for key in ("rediscover", "validate", "save", "jsonPreview", "backupWarning", "copyPath"):
            self.assertIn(f'data-i18n="{key}"', html)
        code = SERVER_PATH.read_text(encoding="utf-8") + (CONFIGURATOR / "app.js").read_text(encoding="utf-8")
        for command in ("subprocess", "os.system", "git add", "git commit", "git push", "git remote", "/api/modules/migrate"):
            self.assertNotIn(command, code.lower())


if __name__ == "__main__":
    unittest.main()
