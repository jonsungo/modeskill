---
name: modeskill
description: Modelab private capability router. Use for UI 一致性分析、参考项目、目标项目、项目画像、一致性报告、跨项目样式漂移, or requests such as 用大白话解释这个项目、这个技术逻辑面试时怎么说、帮我总结项目的技术实现、把代码逻辑翻译成人话、我该怎么向面试官介绍这个项目, extract design conventions, cross-project UI consistency, explain this project in plain language, or summarize the technical implementation for an interview. Git-synced and optional local modules are loaded only when actually installed.
---

# Modeskill

Modeskill is Modelab's unified private Skill. `ui-consistency` is Git-synced; additional capabilities may be optional local modules. Do not claim a module exists until its manifest and files are resolved.

Consistency does not mean visually identical output.
一致不等于视觉完全相同。

## Execution Order

1. Confirm the task.
2. Read `shared/safety-boundaries.md` and `shared/authorization-model.md`.
3. Read `modules.json` and `shared/module-model.md`.
4. Confirm the Workspace root and runtime access, then read `shared/workspace-model.md`.
5. Validate the configuration with `shared/scripts/validate_config.py`.
6. Load the selected module only after resolving its registered path.
7. Build evidence using `shared/evidence-model.md`.
8. Produce a plan before implementation.
9. Check write authorization. References are always read-only; target writing requires `explicit-per-task`, current-task authorization, and runtime write access.
10. Execute within authorization or remain read-only, then produce the report.

A user may authorize one Workspace root containing many projects. Modeskill may discover and read projects inside it without individual reference authorization. The Configurator edits configuration only: it does not grant runtime access or current-task write authorization.

## UI Consistency Routing

- Read `ui-consistency/references/consistency-methodology.md` for analysis.
- Read `ui-consistency/references/source-priority.md` before resolving evidence conflicts.
- Read `ui-consistency/references/decision-taxonomy.md` before classification.
- Read `ui-consistency/references/project-profile-spec.md` for Project Profiles.
- Read `ui-consistency/references/report-format.md` for consistency reports.

## Optional Local Module Routing

For plain-language project explanations or interview summaries, resolve the optional `technical-explainer` registration with `shared/scripts/module_registry.py`. Pass the current Skill entry path, including a user-level symlink path when applicable. The resolver follows the real Skill path, locates the repository by its three markers, and then checks `.local/modules` without searching elsewhere.

If resolution fails or the module is disabled, say exactly: `本机模块未安装或当前 Modeskill 仓库不可访问。` Do not invent another location or pretend the feature is installed. Read only the entry references returned by the local module metadata. Never copy local-module instructions, formats, examples, or sensitive project evidence into Git-tracked reports or fixtures.

## v0.1 Limits

- Project discovery returns project inventory and basic metadata, not a complete UI scan.
- No automatic extraction, drift monitoring, or code modification.
- Controlled writing is a future capability; v0.1 only models and tests authorization decisions.
