#!/usr/bin/env python3
"""Validate a UI consistency report, evidence paths, and summary counts."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = MODULE_DIR.parent
SHARED_SCRIPTS = SKILL_DIR / "shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPTS))

from path_security import PathSecurityError, resolve_inside, workspace_root
from schema_utils import SchemaError, load_json, validate_file


def validate_report(report_path: Path, schema_path: Path, workspace_path: Path) -> None:
    validate_file(schema_path, report_path)
    report = load_json(report_path)
    counts = Counter(item["classification"] for item in report["conclusions"])
    for classification, expected in report["summary"].items():
        if counts[classification] != expected:
            raise SchemaError(f"summary {classification}={expected} but conclusions contain {counts[classification]}")
    workspace = load_json(workspace_path)
    root = workspace_root(workspace_path, workspace["workspace"]["root"])
    paths = list(report["reference_sources"])
    for conclusion in report["conclusions"]:
        paths.extend(item["source_file"] for item in conclusion["evidence"])
    for path in paths:
        resolved = resolve_inside(root, path)
        if not resolved.is_file():
            raise PathSecurityError(f"report evidence is not a file: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Modeskill UI consistency report.")
    parser.add_argument("report", nargs="?", default=MODULE_DIR / "assets" / "consistency-report.example.json", type=Path)
    parser.add_argument("--schema", default=MODULE_DIR / "schemas" / "consistency-report.schema.json", type=Path)
    parser.add_argument("--workspace", default=MODULE_DIR / "assets" / "workspace.example.json", type=Path)
    args = parser.parse_args()
    try:
        validate_report(args.report.resolve(), args.schema.resolve(), args.workspace.resolve())
    except (OSError, ValueError, SchemaError, PathSecurityError) as exc:
        print(f"consistency report invalid: {exc}", file=sys.stderr)
        return 1
    print(f"consistency report valid: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
