#!/usr/bin/env python3
"""Discover projects inside one authorized Workspace root."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Any

from path_security import PathSecurityError, resolve_inside

DEFAULT_MARKERS = [".git", "package.json", "composer.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "build.gradle"]
DEFAULT_EXCLUDED = [".git", "node_modules", "vendor", "dist", "build", ".next", "coverage", "__pycache__", ".venv", "tmp", "temp", ".cache"]


def discover_projects(root: Path, discovery: dict[str, Any], manual_projects: list[dict[str, str]]) -> dict[str, Any]:
    root = root.resolve(strict=True)
    found: dict[str, dict[str, Any]] = {}
    rejected: list[str] = []
    if discovery.get("automatic", True):
        _walk(root, root, 0, discovery, found, rejected)
    for manual in manual_projects:
        try:
            path = resolve_inside(root, manual["path"])
        except PathSecurityError as exc:
            raise PathSecurityError(f"manual project {manual['path']!r}: {exc}") from exc
        if not path.is_dir():
            raise PathSecurityError(f"manual project is not a directory: {manual['path']}")
        relative = _relative(root, path)
        found[relative] = _project(relative, manual.get("name") or path.name or "Workspace", ["manual"], "manual")
    return {"projects": sorted(found.values(), key=lambda item: item["path"]), "rejected_paths": sorted(set(rejected))}


def _walk(root: Path, current: Path, depth: int, config: dict[str, Any], found: dict[str, dict[str, Any]], rejected: list[str]) -> None:
    if depth > config["max_depth"]:
        return
    try:
        resolved = resolve_inside(root, current)
    except PathSecurityError:
        rejected.append(str(current))
        return
    relative = _relative(root, resolved)
    markers = _markers(resolved, config.get("project_markers", DEFAULT_MARKERS))
    is_root = resolved == root
    include = _included(relative, config.get("include_patterns", ["**"]))
    if markers and include and (not is_root or config.get("treat_workspace_root_as_project", False)):
        found[relative] = _project(relative, resolved.name or "Workspace", markers, "automatic")
    if not config.get("recursive", True) or depth == config["max_depth"]:
        return
    if markers and not is_root and not config.get("continue_below_repository_root", True):
        return
    try:
        entries = list(os.scandir(resolved))
    except PermissionError as exc:
        raise PathSecurityError(f"runtime cannot read directory: {resolved}") from exc
    excluded = set(config.get("excluded_directories", DEFAULT_EXCLUDED))
    for entry in entries:
        if not entry.is_dir(follow_symlinks=False) and not entry.is_symlink():
            continue
        child_relative = _relative(root, Path(entry.path), resolve=False)
        if entry.name in excluded or _matches(child_relative, config.get("exclude_patterns", [])):
            continue
        if entry.is_symlink():
            try:
                target = resolve_inside(root, entry.path)
            except PathSecurityError:
                rejected.append(child_relative)
                continue
            if not target.is_dir():
                continue
        _walk(root, Path(entry.path), depth + 1, config, found, rejected)


def _markers(path: Path, configured: list[str]) -> list[str]:
    matched = [marker for marker in configured if (path / marker).exists()]
    has_index = (path / "index.html").is_file()
    has_source = any((path / name).is_dir() for name in ("src", "css", "js", "assets"))
    if has_index and has_source:
        matched.append("index.html+source")
    return sorted(set(matched))


def _included(relative: str, patterns: list[str]) -> bool:
    return relative == "." or not patterns or _matches(relative, patterns)


def _matches(relative: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(relative, pattern) or fnmatch.fnmatch(f"{relative}/", pattern) for pattern in patterns)


def _relative(root: Path, path: Path, *, resolve: bool = True) -> str:
    candidate = path.resolve() if resolve else path
    relative = candidate.relative_to(root)
    return "." if not relative.parts else relative.as_posix()


def _project(path: str, name: str, markers: list[str], source: str) -> dict[str, Any]:
    return {"id": path, "name": name, "path": path, "markers": markers, "source": source}
