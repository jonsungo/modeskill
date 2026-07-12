#!/usr/bin/env python3
"""Validate a Modeskill workspace configuration and its live project roles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from path_security import PathSecurityError, resolve_inside, workspace_root
from schema_utils import SchemaError, load_json, validate_file

SHARED_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SHARED_DIR.parent
DEFAULT_CONFIG = SKILL_DIR / "ui-consistency" / "assets" / "workspace.example.json"


def validate_workspace(config_path: Path, schema_path: Path) -> None:
    validate_file(schema_path, config_path)
    config = load_json(config_path)
    root = workspace_root(config_path, config["workspace"]["root"])
    projects: dict[str, Path] = {}
    for project in config["discovery_cache"]["discovered_projects"]:
        resolved = _project(root, project["path"])
        normalized = resolved.relative_to(root).as_posix() or "."
        if project["id"] != normalized or project["path"] != normalized:
            raise SchemaError(f"discovery cache id/path must equal normalized relative path: {normalized}")
        projects[normalized] = resolved
    for project in config["manual_projects"]:
        resolved = _project(root, project["path"])
        projects[resolved.relative_to(root).as_posix() or "."] = resolved
    selected = [config["roles"]["primary_reference"], *config["roles"]["secondary_references"], config["roles"]["target_project"]]
    if len(selected) != len(set(selected)):
        raise SchemaError("project roles must select distinct projects")
    for project_id in selected:
        if project_id not in projects:
            raise SchemaError(f"selected project is missing from current discovery/manual projects: {project_id}")
        if not projects[project_id].exists():
            raise SchemaError(f"selected project no longer exists: {project_id}")
    for authority in config["authority_mapping"]:
        resolve_inside(root, authority["source"])


def _project(root: Path, value: str) -> Path:
    resolved = resolve_inside(root, value)
    if not resolved.is_dir():
        raise PathSecurityError(f"project is not a directory: {value}")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Modeskill workspace configuration.")
    parser.add_argument("config", nargs="?", default=DEFAULT_CONFIG, type=Path)
    parser.add_argument("--schema", default=SHARED_DIR / "schemas" / "workspace.schema.json", type=Path)
    args = parser.parse_args()
    try:
        validate_workspace(args.config.resolve(), args.schema.resolve())
    except (OSError, ValueError, SchemaError, PathSecurityError) as exc:
        print(f"workspace config invalid: {exc}", file=sys.stderr)
        return 1
    print(f"workspace config valid: {args.config}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
