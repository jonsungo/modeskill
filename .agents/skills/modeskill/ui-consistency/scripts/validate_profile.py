#!/usr/bin/env python3
"""Validate a UI consistency Project Profile and its evidence paths."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

MODULE_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = MODULE_DIR.parent
SHARED_SCRIPTS = SKILL_DIR / "shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPTS))

from path_security import PathSecurityError, resolve_inside, workspace_root
from schema_utils import SchemaError, load_json, validate_file


def validate_profile(profile_path: Path, schema_path: Path, workspace_path: Path) -> None:
    validate_file(schema_path, profile_path)
    profile = load_json(profile_path)
    workspace = load_json(workspace_path)
    root = workspace_root(workspace_path, workspace["workspace"]["root"])
    paths = [source["path"] for source in profile["source_files"]]
    paths.extend(_evidence_paths(profile))
    for path in paths:
        resolved = resolve_inside(root, path)
        if not resolved.is_file():
            raise PathSecurityError(f"evidence is not a file: {path}")


def _evidence_paths(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        if "source_file" in value:
            found.append(value["source_file"])
        for child in value.values():
            found.extend(_evidence_paths(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_evidence_paths(child))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Modeskill UI Project Profile.")
    parser.add_argument("profile", nargs="?", default=MODULE_DIR / "assets" / "project-profile.example.json", type=Path)
    parser.add_argument("--schema", default=MODULE_DIR / "schemas" / "project-profile.schema.json", type=Path)
    parser.add_argument("--workspace", default=MODULE_DIR / "assets" / "workspace.example.json", type=Path)
    args = parser.parse_args()
    try:
        validate_profile(args.profile.resolve(), args.schema.resolve(), args.workspace.resolve())
    except (OSError, ValueError, SchemaError, PathSecurityError) as exc:
        print(f"project profile invalid: {exc}", file=sys.stderr)
        return 1
    print(f"project profile valid: {args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
