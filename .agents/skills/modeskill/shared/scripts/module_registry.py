#!/usr/bin/env python3
"""Locate Modeskill and safely load local module registration."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from path_security import PathSecurityError, resolved_directory, safe_local_subdirectory, safe_relative_file

MODULE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
UNAVAILABLE_MESSAGE = "本机模块未安装或当前 Modeskill 仓库不可访问。"
DISABLED_MESSAGE = "本机模块已安装但当前已停用。"
INVALID_MESSAGE = "本机模块配置无效。"
UNSAFE_MESSAGE = "本机模块路径不安全。"


class ModuleRegistryError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def find_repository_root(skill_path: Path) -> Path:
    try:
        resolved = skill_path.expanduser().resolve(strict=True)
    except OSError as exc:
        raise ModuleRegistryError(UNAVAILABLE_MESSAGE, code="repository-unavailable") from exc
    start = resolved.parent if resolved.is_file() else resolved
    for candidate in (start, *start.parents):
        if _is_repository_root(candidate):
            return resolved_directory(candidate, label="repository root")
    raise ModuleRegistryError(UNAVAILABLE_MESSAGE, code="repository-unavailable")


def load_synced_modules(repository_root: Path) -> list[dict[str, Any]]:
    root = resolved_directory(repository_root, label="repository root")
    skill_root = resolved_directory(root / ".agents" / "skills" / "modeskill", within=root, label="Skill directory")
    data, _ = _load_json_file(skill_root, "modules.json", label="module manifest")
    modules = data.get("modules")
    if not isinstance(modules, list):
        raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-manifest")
    for module in modules:
        if not isinstance(module, dict):
            raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-manifest")
        module_id = validate_module_id(module.get("id"))
        if module.get("distribution") != "git-synced":
            raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-manifest")
        path = module.get("path")
        if not isinstance(path, str) or not path:
            raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-manifest")
        try:
            resolved_directory(skill_root / path, within=skill_root, label=f"Git module {module_id}")
        except PathSecurityError as exc:
            raise ModuleRegistryError(UNSAFE_MESSAGE, code="unsafe-module-path") from exc
    return modules


def load_local_modules(repository_root: Path, *, require_registry: bool = False) -> list[dict[str, Any]]:
    try:
        modules_root = _local_modules_root(repository_root, create=False)
    except ModuleRegistryError as exc:
        if exc.code == "not-installed" and not require_registry:
            return []
        raise
    registry_candidate = modules_root / "registry.json"
    if not registry_candidate.exists() and not registry_candidate.is_symlink():
        if require_registry:
            raise ModuleRegistryError(UNAVAILABLE_MESSAGE, code="not-installed")
        return []
    registry, _ = _load_json_file(modules_root, "registry.json", label="local module registry")
    entries = registry.get("modules")
    if not isinstance(entries, list):
        raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-registry")
    modules: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-registry")
        module_id = validate_module_id(entry.get("id"))
        enabled = _strict_boolean(entry.get("enabled"), code="invalid-registry")
        path = entry.get("path")
        if not isinstance(path, str) or Path(path).is_absolute() or Path(path).parts != (module_id,):
            raise ModuleRegistryError(UNSAFE_MESSAGE, code="unsafe-module-path")
        try:
            module_path = resolved_directory(modules_root / path, within=modules_root, label="local module")
        except PathSecurityError as exc:
            raise ModuleRegistryError(UNSAFE_MESSAGE, code="unsafe-module-path") from exc
        metadata, _ = _load_json_file(module_path, "module.json", label="local module metadata")
        if metadata.get("id") != module_id or metadata.get("distribution") != "local-only":
            raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-module-metadata")
        _strict_boolean(metadata.get("enabled"), code="invalid-module-metadata")
        entry_references = metadata.get("entry_references")
        if not isinstance(entry_references, list) or not entry_references:
            raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-entry-references")
        resolved_entries: list[str] = []
        for reference in entry_references:
            if not isinstance(reference, str) or not reference:
                raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-entry-references")
            try:
                resolved_entries.append(str(safe_relative_file(module_path, reference, label="module entry reference")))
            except PathSecurityError as exc:
                raise ModuleRegistryError(UNSAFE_MESSAGE, code="unsafe-entry-reference") from exc
        modules.append({**metadata, "entry_references": resolved_entries, "enabled": enabled, "path": str(module_path)})
    return modules


def set_local_module_enabled(repository_root: Path, module_id: str, enabled: bool) -> Path:
    module_id = validate_module_id(module_id)
    enabled = _strict_boolean(enabled, code="invalid-enabled")
    installed = load_local_modules(repository_root, require_registry=True)
    if not any(module["id"] == module_id for module in installed):
        raise ModuleRegistryError(UNAVAILABLE_MESSAGE, code="not-installed")
    modules_root = _local_modules_root(repository_root, create=False)
    registry, registry_path = _load_json_file(modules_root, "registry.json", label="local module registry")
    entries = registry.get("modules")
    if not isinstance(entries, list):
        raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-registry")
    matched = False
    for entry in entries:
        if not isinstance(entry, dict):
            raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-registry")
        _strict_boolean(entry.get("enabled"), code="invalid-registry")
        if entry.get("id") == module_id:
            entry["enabled"] = enabled
            matched = True
    if not matched:
        raise ModuleRegistryError(UNAVAILABLE_MESSAGE, code="not-installed")
    if registry_path.is_symlink():
        raise ModuleRegistryError(UNSAFE_MESSAGE, code="unsafe-registry-path")
    _atomic_json(modules_root, registry_path, registry)
    return registry_path


def validate_module_id(module_id: Any) -> str:
    if not isinstance(module_id, str) or not MODULE_ID.fullmatch(module_id):
        raise ModuleRegistryError(INVALID_MESSAGE, code="invalid-module-id")
    return module_id


def local_modules_path(repository_root: Path) -> Path:
    return _local_modules_root(repository_root, create=True)


def _is_repository_root(candidate: Path) -> bool:
    return (
        (candidate / "AGENTS.md").is_file()
        and (candidate / "README.md").is_file()
        and (candidate / ".agents" / "skills" / "modeskill" / "SKILL.md").is_file()
    )


def _local_modules_root(repository_root: Path, *, create: bool) -> Path:
    root = resolved_directory(repository_root, label="repository root")
    local_candidate = root / ".local"
    modules_candidate = local_candidate / "modules"
    if not create and not local_candidate.exists() and not local_candidate.is_symlink():
        raise ModuleRegistryError(UNAVAILABLE_MESSAGE, code="not-installed")
    if not create and not modules_candidate.exists() and not modules_candidate.is_symlink():
        raise ModuleRegistryError(UNAVAILABLE_MESSAGE, code="not-installed")
    try:
        _, modules = safe_local_subdirectory(root, "modules", create=create)
    except PathSecurityError as exc:
        raise ModuleRegistryError(UNSAFE_MESSAGE, code="unsafe-local-path") from exc
    return modules


def _load_json_file(parent: Path, relative: str, *, label: str) -> tuple[dict[str, Any], Path]:
    try:
        path = safe_relative_file(parent, relative, label=label)
    except PathSecurityError as exc:
        raise ModuleRegistryError(UNSAFE_MESSAGE, code=f"unsafe-{label.replace(' ', '-')}") from exc
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ModuleRegistryError(INVALID_MESSAGE, code=f"invalid-{label.replace(' ', '-')}") from exc
    if not isinstance(data, dict):
        raise ModuleRegistryError(INVALID_MESSAGE, code=f"invalid-{label.replace(' ', '-')}")
    return data, path


def _strict_boolean(value: Any, *, code: str) -> bool:
    if type(value) is not bool:
        raise ModuleRegistryError(INVALID_MESSAGE, code=code)
    return value


def _atomic_json(parent: Path, destination: Path, data: dict[str, Any]) -> None:
    parent = resolved_directory(parent, label="module registry directory")
    if destination.parent.resolve(strict=True) != parent or destination.is_symlink():
        raise ModuleRegistryError(UNSAFE_MESSAGE, code="unsafe-registry-path")
    fd, temporary = tempfile.mkstemp(prefix=".modeskill-modules-", suffix=".tmp", dir=parent)
    temporary_path = Path(temporary)
    try:
        if not temporary_path.resolve(strict=True).is_relative_to(parent):
            raise ModuleRegistryError(UNSAFE_MESSAGE, code="unsafe-temporary-path")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve a Modeskill local module from a Skill path.")
    parser.add_argument("--skill-path", required=True, type=Path)
    parser.add_argument("--module", required=True)
    args = parser.parse_args()
    try:
        repository_root = find_repository_root(args.skill_path)
        module_id = validate_module_id(args.module)
        installed = next((item for item in load_local_modules(repository_root, require_registry=True) if item["id"] == module_id), None)
        if installed is None:
            raise ModuleRegistryError(UNAVAILABLE_MESSAGE, code="not-installed")
        if not installed["enabled"]:
            raise ModuleRegistryError(DISABLED_MESSAGE, code="disabled")
    except ModuleRegistryError as exc:
        print(str(exc))
        return 1
    print(json.dumps({"repository_root": str(repository_root), "module": installed}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
