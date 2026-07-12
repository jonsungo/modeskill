#!/usr/bin/env python3
"""Safely read and atomically store local Workspace configuration."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from path_security import PathSecurityError, resolved_directory, safe_local_subdirectory, safe_relative_file

SAFE_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$")


def config_filename(name: str) -> str:
    if not isinstance(name, str) or not SAFE_NAME.fullmatch(name) or ".." in name:
        raise ValueError("invalid workspace name")
    return f"{name}.json"


def save_config(repository_root: Path, name: str, data: dict[str, Any]) -> Path:
    if not isinstance(data, dict):
        raise ValueError("configuration must be an object")
    root = resolved_directory(repository_root, label="repository root")
    try:
        _, directory = safe_local_subdirectory(root, "workspaces", create=True)
    except PathSecurityError as exc:
        raise ValueError("unsafe local Workspace storage") from exc
    filename = config_filename(name)
    destination = directory / filename
    if destination.is_symlink():
        raise ValueError("Workspace configuration cannot be a symbolic link")
    if destination.exists():
        safe_relative_file(directory, filename, label="Workspace configuration")
    if destination.parent.resolve(strict=True) != directory:
        raise ValueError("unsafe Workspace configuration parent")
    fd, temporary = tempfile.mkstemp(prefix=".modeskill-", suffix=".tmp", dir=directory)
    temporary_path = Path(temporary)
    try:
        if not temporary_path.resolve(strict=True).is_relative_to(directory):
            raise ValueError("unsafe temporary configuration path")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise
    return destination


def load_config(repository_root: Path, name: str) -> dict[str, Any]:
    root = resolved_directory(repository_root, label="repository root")
    try:
        _, directory = safe_local_subdirectory(root, "workspaces", create=False)
        path = safe_relative_file(directory, config_filename(name), label="Workspace configuration")
    except PathSecurityError as exc:
        raise ValueError("unsafe or unavailable Workspace configuration") from exc
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("invalid Workspace configuration") from exc
    if not isinstance(data, dict):
        raise ValueError("configuration must be an object")
    return data
