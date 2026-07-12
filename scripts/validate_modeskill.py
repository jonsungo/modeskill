#!/usr/bin/env python3
"""Repository-level integrity validation for Modeskill v0.1."""

from __future__ import annotations

import subprocess
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "modeskill"
UI = SKILL / "ui-consistency"

REQUIRED_FILES = [
    "AGENTS.md", "README.md", "CHANGELOG.md", ".gitignore",
    ".agents/skills/modeskill/SKILL.md",
    ".agents/skills/modeskill/modules.json",
    ".agents/skills/modeskill/shared/safety-boundaries.md",
    ".agents/skills/modeskill/shared/authorization-model.md",
    ".agents/skills/modeskill/shared/workspace-model.md",
    ".agents/skills/modeskill/shared/evidence-model.md",
    ".agents/skills/modeskill/shared/module-model.md",
    ".agents/skills/modeskill/shared/schemas/workspace.schema.json",
    ".agents/skills/modeskill/shared/scripts/schema_utils.py",
    ".agents/skills/modeskill/shared/scripts/path_security.py",
    ".agents/skills/modeskill/shared/scripts/project_discovery.py",
    ".agents/skills/modeskill/shared/scripts/config_storage.py",
    ".agents/skills/modeskill/shared/scripts/module_registry.py",
    ".agents/skills/modeskill/shared/scripts/validate_config.py",
    ".agents/skills/modeskill/ui-consistency/references/consistency-methodology.md",
    ".agents/skills/modeskill/ui-consistency/references/source-priority.md",
    ".agents/skills/modeskill/ui-consistency/references/decision-taxonomy.md",
    ".agents/skills/modeskill/ui-consistency/references/project-profile-spec.md",
    ".agents/skills/modeskill/ui-consistency/references/report-format.md",
    ".agents/skills/modeskill/ui-consistency/schemas/project-profile.schema.json",
    ".agents/skills/modeskill/ui-consistency/schemas/consistency-report.schema.json",
    ".agents/skills/modeskill/ui-consistency/assets/workspace.example.json",
    ".agents/skills/modeskill/ui-consistency/assets/project-profile.example.json",
    ".agents/skills/modeskill/ui-consistency/assets/consistency-report.example.json",
    ".agents/skills/modeskill/ui-consistency/assets/consistency-report.example.md",
    ".agents/skills/modeskill/ui-consistency/scripts/validate_profile.py",
    ".agents/skills/modeskill/ui-consistency/scripts/validate_report.py",
    ".agents/skills/modeskill/configurator/server.py",
    ".agents/skills/modeskill/configurator/index.html",
    ".agents/skills/modeskill/configurator/app.js",
    ".agents/skills/modeskill/configurator/i18n.js",
    ".agents/skills/modeskill/configurator/styles.css",
    "examples/reference-project/index.html", "examples/reference-project/app.js",
    "examples/target-project/index.html", "examples/target-project/app.js",
    "docs/v0.1-usage.md", "docs/safety-boundaries.md",
]

FORBIDDEN_MODULES = ["page-safety-consistency", "data-interface-consistency", "memory-store", "code-natural-language"]


def main() -> int:
    failures = [f"missing required file: {path}" for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    failures.extend(f"unimplemented module directory must not exist: {name}" for name in FORBIDDEN_MODULES if (SKILL / name).exists())
    if failures:
        return finish(failures)
    for script in (
        SKILL / "shared" / "scripts" / "validate_config.py",
        UI / "scripts" / "validate_profile.py",
        UI / "scripts" / "validate_report.py",
    ):
        failures.extend(run_validator(script))
    failures.extend(validate_skill())
    failures.extend(validate_markdown_report())
    failures.extend(validate_local_storage())
    failures.extend(validate_modules())
    failures.extend(validate_local_privacy())
    return finish(failures)


def run_validator(script: Path) -> list[str]:
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, text=True, capture_output=True, check=False)
    return [] if result.returncode == 0 else [f"{script.relative_to(ROOT)} failed: {result.stderr.strip()}"]


def validate_skill() -> list[str]:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    required = ["name: modeskill", "UI 一致性分析", "Consistency does not mean visually identical output.", "一致不等于视觉完全相同。", "explicit-per-task", "本机模块未安装或当前 Modeskill 仓库不可访问。"]
    return [f"SKILL.md missing: {item}" for item in required if item not in text]


def validate_markdown_report() -> list[str]:
    text = (UI / "assets" / "consistency-report.example.md").read_text(encoding="utf-8")
    sections = ["## Reference Sources", "## Inherited Rules", "## Adapted Rules", "## Project-specific Rules", "## Unresolved Conflicts", "## Deprecated Patterns", "## Implementation Recommendations", "## Files That Would Be Affected", "## Risk And Write Authorization", "## Known Limits"]
    return [f"report missing section: {section}" for section in sections if section not in text]


def validate_local_storage() -> list[str]:
    ignored_paths = [".local/workspaces/example.json", ".local/modules/example/module.json"]
    tracked = subprocess.run(["git", "ls-files", ".local"], cwd=ROOT, text=True, capture_output=True, check=False)
    failures = []
    for path in ignored_paths:
        ignored = subprocess.run(["git", "check-ignore", path], cwd=ROOT, text=True, capture_output=True, check=False)
        if ignored.returncode != 0:
            failures.append(f"local path is not ignored by Git: {path}")
    if tracked.stdout.strip():
        failures.append(".local contains Git-tracked files")
    return failures


def validate_modules() -> list[str]:
    failures = []
    manifest = json.loads((SKILL / "modules.json").read_text(encoding="utf-8"))
    for module in manifest.get("modules", []):
        if module.get("distribution") != "git-synced":
            failures.append(f"modules.json contains a non-synced module: {module.get('id')}")
        if not (SKILL / module.get("path", "")).is_dir():
            failures.append(f"Git-synced module is missing: {module.get('id')}")
    forbidden_id = "technical" + "-explainer"
    if any(module.get("id") == forbidden_id for module in manifest.get("modules", [])):
        failures.append("local-only module appears in modules.json")
    sys.path.insert(0, str(SKILL / "shared" / "scripts"))
    from module_registry import ModuleRegistryError, load_local_modules
    local_root = ROOT / ".local" / "modules"
    if local_root.exists():
        try:
            load_local_modules(ROOT)
        except ModuleRegistryError as exc:
            failures.append(f"local module registry invalid: {exc}")
    return failures


def validate_local_privacy() -> list[str]:
    failures = []
    user_path_marker = "/" + "Users/"
    proprietary_markers = [
        "# Technical " + "Explainer",
        "# Output " + "Formats",
        "Explain project " + "implementation for a designer who uses vibe coding",
        "Never describe phpMyAdmin " + "as the database",
        "Use roughly 20-40 Chinese " + "characters for a quick interviewer question",
    ]
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or ".local" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if user_path_marker in text:
            failures.append(f"user-specific absolute path found: {path.relative_to(ROOT)}")
        for marker in proprietary_markers:
            if marker in text:
                failures.append(f"local-only proprietary content copied outside .local: {path.relative_to(ROOT)}")
        if path.suffix == ".json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = None
            if _contains_local_module_identity(data):
                failures.append(f"local-only module metadata copied outside .local: {path.relative_to(ROOT)}")
        if path.name == "generic-project.example.json":
            failures.append(f"local-only example copied outside .local: {path.relative_to(ROOT)}")
    code = "\n".join((SKILL / "configurator" / name).read_text(encoding="utf-8") for name in ("server.py", "app.js"))
    for command in ("git add", "git commit", "git push", "git remote", "/api/modules/migrate"):
        if command in code.lower():
            failures.append(f"Configurator contains forbidden Git or migration operation: {command}")
    return failures


def _contains_local_module_identity(value: object) -> bool:
    forbidden_id = "technical" + "-explainer"
    if isinstance(value, dict):
        if value.get("id") == forbidden_id or (value.get("distribution") == "local-only" and "entry_references" in value):
            return True
        return any(_contains_local_module_identity(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_local_module_identity(child) for child in value)
    return False


def finish(failures: list[str]) -> int:
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Modeskill v0.1 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
