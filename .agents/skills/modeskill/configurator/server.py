#!/usr/bin/env python3
"""Local-only, standard-library Modeskill workspace configurator."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

CONFIGURATOR_DIR = Path(__file__).resolve().parent
SKILL_DIR = CONFIGURATOR_DIR.parent
SHARED_SCRIPTS = SKILL_DIR / "shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPTS))

from config_storage import save_config
from module_registry import ModuleRegistryError, find_repository_root, load_local_modules, load_synced_modules, local_modules_path, set_local_module_enabled
from path_security import PathSecurityError, resolve_inside, workspace_root
from project_discovery import discover_projects
from schema_utils import SchemaError, validate_document

REPO_ROOT = find_repository_root(SKILL_DIR / "SKILL.md")
SCHEMA = json.loads((SKILL_DIR / "shared" / "schemas" / "workspace.schema.json").read_text(encoding="utf-8"))
MAX_BODY = 1_000_000


class ApiError(ValueError):
    def __init__(self, status: int, code: str) -> None:
        super().__init__(code)
        self.status = status
        self.code = code


def validate_host(host: str | None, port: int) -> None:
    allowed = {"127.0.0.1", "localhost", f"127.0.0.1:{port}", f"localhost:{port}"}
    if not isinstance(host, str) or host.strip().lower() not in allowed:
        raise ApiError(403, "invalid_host")


def validate_origin(origin: str | None, port: int, client_host: str) -> None:
    if origin is None:
        if client_host not in {"127.0.0.1", "::1"}:
            raise ApiError(403, "missing_origin")
        return
    allowed = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
    if origin.strip().lower() not in allowed:
        raise ApiError(403, "invalid_origin")


def parse_json_payload(content_type: str | None, content_length: str | None, reader: Callable[[int], bytes]) -> dict[str, Any]:
    media_type = content_type.split(";", 1)[0].strip().lower() if isinstance(content_type, str) else ""
    if media_type != "application/json":
        raise ApiError(415, "json_required")
    try:
        length = int(content_length or "0")
    except (TypeError, ValueError) as exc:
        raise ApiError(400, "invalid_content_length") from exc
    if length > MAX_BODY:
        raise ApiError(413, "request_too_large")
    if length <= 0:
        raise ApiError(400, "empty_request")
    try:
        payload = json.loads(reader(length).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiError(400, "invalid_json") from exc
    if not isinstance(payload, dict):
        raise ApiError(400, "json_object_required")
    return payload


def validate_discovery_request(payload: dict[str, Any]) -> None:
    workspace = payload.get("workspace")
    discovery = payload.get("discovery")
    manual = payload.get("manual_projects")
    if not isinstance(workspace, dict) or not isinstance(workspace.get("root"), str) or not workspace["root"]:
        raise ApiError(400, "invalid_discovery_request")
    if not isinstance(discovery, dict) or not isinstance(manual, list):
        raise ApiError(400, "invalid_discovery_request")
    boolean_fields = ["automatic", "recursive", "treat_workspace_root_as_project", "continue_below_repository_root"]
    if any(type(discovery.get(field)) is not bool for field in boolean_fields):
        raise ApiError(400, "invalid_discovery_request")
    depth = discovery.get("max_depth")
    if type(depth) is not int or not 0 <= depth <= 20:
        raise ApiError(400, "invalid_discovery_request")
    for field in ("project_markers", "include_patterns", "exclude_patterns", "excluded_directories"):
        value = discovery.get(field)
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            raise ApiError(400, "invalid_discovery_request")
    for project in manual:
        if (
            not isinstance(project, dict)
            or not isinstance(project.get("name"), str)
            or not project["name"]
            or not isinstance(project.get("path"), str)
            or not project["path"]
        ):
            raise ApiError(400, "invalid_discovery_request")


def validate_module_toggle(payload: dict[str, Any]) -> tuple[str, bool]:
    module_id = payload.get("module_id")
    enabled = payload.get("enabled")
    if not isinstance(module_id, str) or not module_id or type(enabled) is not bool:
        raise ApiError(400, "invalid_module_toggle")
    return module_id, enabled


def validate_payload(config: dict[str, Any]) -> Path:
    validate_document(SCHEMA, config)
    root = workspace_root(REPO_ROOT / ".local" / "workspaces" / "pending.json", config["workspace"]["root"])
    discovered = set()
    for item in config["discovery_cache"]["discovered_projects"]:
        path = resolve_inside(root, item["path"])
        normalized = path.relative_to(root).as_posix() or "."
        if item["id"] != normalized or item["path"] != normalized:
            raise SchemaError("discovery cache path is not normalized")
        discovered.add(normalized)
    manual = set()
    for item in config["manual_projects"]:
        path = resolve_inside(root, item["path"])
        manual.add(path.relative_to(root).as_posix() or ".")
    available = discovered | manual
    selected = [config["roles"]["primary_reference"], *config["roles"]["secondary_references"], config["roles"]["target_project"]]
    if len(selected) != len(set(selected)):
        raise SchemaError("project roles must be distinct")
    if any(item not in available or not resolve_inside(root, item).is_dir() for item in selected):
        raise SchemaError("selected project is unavailable")
    for authority in config["authority_mapping"]:
        resolve_inside(root, authority["source"])
    return root


def modules_payload() -> dict[str, Any]:
    local_root = local_modules_path(REPO_ROOT)
    synced = [{**item, "installed": True, "path": f".agents/skills/modeskill/{item['path']}"} for item in load_synced_modules(REPO_ROOT)]
    local = [{**item, "installed": True, "implemented": True} for item in load_local_modules(REPO_ROOT)]
    return {"modules": synced + local, "local_modules_path": str(local_root), "workspace_config_path": ".local/workspaces"}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        try:
            self._validate_host()
            path = urlparse(self.path).path
            if path == "/api/modules":
                self._json(200, modules_payload())
                return
            filename = {"/": "index.html", "/app.js": "app.js", "/i18n.js": "i18n.js", "/styles.css": "styles.css"}.get(path)
            if not filename:
                raise ApiError(404, "not_found")
            content_type = {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}[Path(filename).suffix]
            data = (CONFIGURATOR_DIR / filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            self._send_error(exc)

    def do_POST(self) -> None:
        try:
            self._validate_host()
            validate_origin(self.headers.get("Origin"), self.server.server_port, self.client_address[0])
            payload = self._payload()
            path = urlparse(self.path).path
            if path == "/api/discover":
                validate_discovery_request(payload)
                root = workspace_root(REPO_ROOT / ".local" / "workspaces" / "pending.json", payload["workspace"]["root"])
                result = discover_projects(root, payload["discovery"], payload["manual_projects"])
                result["discovered_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                self._json(200, result)
            elif path == "/api/validate":
                validate_payload(payload)
                self._json(200, {"valid": True})
            elif path == "/api/save":
                validate_payload(payload)
                destination = save_config(REPO_ROOT, payload["workspace"]["name"], payload)
                self._json(200, {"saved": str(destination.relative_to(REPO_ROOT))})
            elif path == "/api/modules/toggle":
                module_id, enabled = validate_module_toggle(payload)
                set_local_module_enabled(REPO_ROOT, module_id, enabled)
                self._json(200, {"updated": True})
            else:
                raise ApiError(404, "not_found")
        except Exception as exc:
            self._send_error(exc)

    def do_OPTIONS(self) -> None:
        self._method_not_allowed()

    def do_PUT(self) -> None:
        self._method_not_allowed()

    def do_PATCH(self) -> None:
        self._method_not_allowed()

    def do_DELETE(self) -> None:
        self._method_not_allowed()

    def _method_not_allowed(self) -> None:
        try:
            self._validate_host()
            raise ApiError(405, "method_not_allowed")
        except Exception as exc:
            self._send_error(exc)

    def _validate_host(self) -> None:
        validate_host(self.headers.get("Host"), self.server.server_port)

    def _payload(self) -> dict[str, Any]:
        return parse_json_payload(self.headers.get("Content-Type"), self.headers.get("Content-Length"), self.rfile.read)

    def _send_error(self, exc: Exception) -> None:
        if isinstance(exc, ApiError):
            status, code = exc.status, exc.code
        elif isinstance(exc, ModuleRegistryError):
            status, code = 400, "module_configuration_error"
        elif isinstance(exc, PathSecurityError):
            status, code = 400, "unsafe_path"
        elif isinstance(exc, SchemaError):
            status, code = 400, "invalid_configuration"
        elif isinstance(exc, (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError)):
            status, code = 400, "invalid_request"
        else:
            status, code = 500, "internal_error"
        self._json(status, {"error": {"code": code}})

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        return


def create_server(port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main() -> None:
    server = create_server()
    print("Modeskill Configurator: http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
