# Module Distribution Model

Modeskill supports two fixed storage strategies:

- `git-synced`: the module lives under `.agents/skills/modeskill/<module-id>/` and may be tracked by the repository. The Configurator never commits or pushes it.
- `local-only`: the module lives under `<repository-root>/.local/modules/<module-id>/` and is excluded by `.gitignore`.

Read `modules.json` for Git-synced modules. Locate the repository root from the resolved Skill path before reading `.local/modules/registry.json`. Do not infer a local module from documentation: if registration or files are missing, report `本机模块未安装或当前 Modeskill 仓库不可访问。`

Distribution is informational and fixed in v0.1. The Configurator does not migrate modules, alter Git history, or grant Git permissions. Local modules and Workspace configuration require manual backup before deleting the repository or moving to another computer.
