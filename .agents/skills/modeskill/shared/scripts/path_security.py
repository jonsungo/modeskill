#!/usr/bin/env python3
"""Resolved-path and per-task authorization checks for Modeskill."""

from __future__ import annotations

import os
import stat
from pathlib import Path


class PathSecurityError(ValueError):
    pass


def resolved_directory(path: Path, *, within: Path | None = None, label: str = "directory") -> Path:
    try:
        resolved = path.expanduser().resolve(strict=True)
    except OSError as exc:
        raise PathSecurityError(f"{label} is unavailable") from exc
    if not resolved.is_dir():
        raise PathSecurityError(f"{label} is not a directory")
    if within is not None and not resolved.is_relative_to(within.resolve(strict=True)):
        raise PathSecurityError(f"{label} escapes its allowed directory")
    return resolved


def safe_child_directory(parent: Path, name: str, *, create: bool, label: str) -> Path:
    parent = resolved_directory(parent, label=f"{label} parent")
    if not name or Path(name).parts != (name,) or name in {".", ".."}:
        raise PathSecurityError(f"invalid {label} name")
    candidate = parent / name
    if candidate.exists() or candidate.is_symlink():
        return resolved_directory(candidate, within=parent, label=label)
    if not create:
        raise PathSecurityError(f"{label} is unavailable")
    candidate.mkdir()
    return resolved_directory(candidate, within=parent, label=label)


def safe_relative_file(parent: Path, relative: str | Path, *, label: str) -> Path:
    parent = resolved_directory(parent, label=f"{label} parent")
    value = Path(relative)
    if not str(relative) or value.is_absolute() or ".." in value.parts:
        raise PathSecurityError(f"invalid {label} path")
    try:
        resolved = (parent / value).resolve(strict=True)
    except OSError as exc:
        raise PathSecurityError(f"{label} is unavailable") from exc
    if not resolved.is_relative_to(parent):
        raise PathSecurityError(f"{label} escapes its allowed directory")
    try:
        mode = resolved.stat().st_mode
    except OSError as exc:
        raise PathSecurityError(f"{label} is unavailable") from exc
    if not stat.S_ISREG(mode):
        raise PathSecurityError(f"{label} is not a regular file")
    return resolved


def safe_local_subdirectory(repository_root: Path, name: str, *, create: bool) -> tuple[Path, Path]:
    root = resolved_directory(repository_root, label="repository root")
    local = safe_child_directory(root, ".local", create=create, label="local directory")
    child = safe_child_directory(local, name, create=create, label=f"local {name} directory")
    return local, child


def workspace_root(config_path: Path, configured_root: str) -> Path:
    candidate = Path(configured_root).expanduser()
    if not candidate.is_absolute():
        candidate = config_path.resolve().parent / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise PathSecurityError(f"workspace root is unavailable: {exc}") from exc
    if not resolved.is_dir():
        raise PathSecurityError("workspace root is not a directory")
    if not os.access(resolved, os.R_OK | os.X_OK):
        raise PathSecurityError("workspace root exists but the runtime cannot read it")
    return resolved


def resolve_inside(root: Path, candidate: str | Path, *, must_exist: bool = True) -> Path:
    root = root.resolve(strict=True)
    path = Path(candidate).expanduser()
    if not path.is_absolute():
        path = root / path
    try:
        resolved = path.resolve(strict=must_exist)
    except OSError as exc:
        raise PathSecurityError(f"path is unavailable: {exc}") from exc
    if not resolved.is_relative_to(root):
        raise PathSecurityError(f"path escapes Workspace root: {candidate}")
    return resolved


def check_project_access(
    project: Path,
    *,
    role: str,
    operation: str,
    target_write_policy: str,
    current_task_authorized: bool = False,
    requested_path: Path | None = None,
) -> tuple[bool, str]:
    if requested_path is not None:
        try:
            resolve_inside(project, requested_path, must_exist=operation == "read")
        except PathSecurityError:
            return (False, "requested path is outside the selected project")
    if operation == "read":
        return (os.access(project, os.R_OK), "runtime read permission")
    if operation != "write":
        return (False, "unsupported operation")
    if role in {"primary-reference", "secondary-reference", "other"}:
        return (False, "reference and non-target projects are always read-only")
    if role != "target":
        return (False, "unknown project role")
    if target_write_policy != "explicit-per-task":
        return (False, "configuration does not allow per-task target writing")
    if not current_task_authorized:
        return (False, "current task has no explicit write authorization")
    if not os.access(project, os.W_OK):
        return (False, "runtime cannot write the target project")
    return (True, "target write authorized for the current task")
