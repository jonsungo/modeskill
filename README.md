# Modeskill

Modeskill is a local-first Skill for helping coding agents keep UI and interaction patterns consistent across multiple projects.

It is designed for people who maintain several related projects and want new pages, components, and workflows to feel consistent with existing products — without blindly copying CSS or forcing every project to use the same fixed template.

Modeskill analyzes a user-defined workspace, compares reference projects with a target project, and helps an agent decide which UI rules should be inherited, adapted, kept project-specific, marked unresolved, or avoided as deprecated.

> Modeskill is not a design system package.  
> It is a consistency method for coding agents.

---

## What Modeskill does

Modeskill helps answer questions like:

- Which project should be treated as the main UI reference?
- Which typography, color, spacing, component, and interaction rules are shared across projects?
- Which differences are intentional and project-specific?
- Which UI rules are only weak evidence and should not be treated as global standards?
- How should a new project stay consistent with existing projects without copying everything?
- Which files would likely be affected if a UI consistency refinement is implemented?

Current v0.1 focuses on workspace configuration, project discovery, UI consistency methodology, safety boundaries, schemas, validation, and a local settings interface.

---

## Core concepts

### Workspace

A Workspace is a local folder that contains one or more projects.

It can be a folder containing multiple independent projects:

```text
workspace/
├── project-a/
├── project-b/
└── project-c/
```

It can also be a single Git repository that contains multiple subprojects:

```text
workspace/
├── .git/
├── project-a/
├── project-b/
└── project-c/
```

Modeskill can discover projects automatically and also allows manual project registration when a project does not have common markers such as `package.json` or `.git`.

---

### Project roles

Inside a workspace, projects can be assigned different roles:

| Role | Meaning |
|---|---|
| Primary reference | The main project used as the strongest UI consistency reference |
| Secondary references | Additional projects used for comparison and supporting evidence |
| Target project | The project being analyzed or refined |

Reference projects are always read-only.

The target project is also read-only by default. Future controlled write workflows require explicit task-level authorization.

---

### UI consistency dimensions

Modeskill v0.1 defines these UI consistency dimensions:

- Typography and text hierarchy
- Color semantics
- Spacing
- Components
- Forms
- Modal behavior
- Responsive behavior
- Engineering conventions

A consistency conclusion can be classified as:

| Classification | Meaning |
|---|---|
| `inherited` | Strong evidence that the rule should be reused |
| `adapted` | The rule should be adjusted for the target project |
| `project-specific` | The difference is intentional for this project |
| `unresolved` | Evidence is not enough to make a safe decision |
| `deprecated` | The rule should not be propagated |

---

## What v0.1 can and cannot do

### v0.1 can

- Define a workspace root
- Discover multiple projects inside that workspace
- Support one Git repository containing multiple subprojects
- Combine automatic discovery with manual project registration
- Assign primary reference, secondary reference, and target project roles
- Store local workspace configuration
- Provide a local settings UI
- Validate workspace, project profile, and consistency report schemas
- Provide example reference and target projects
- Enforce read-only reference project rules
- Load Git-synced modules safely
- Support optional local-only modules without committing them to Git

### v0.1 does not yet

- Automatically extract a complete design system from real projects
- Automatically monitor UI drift
- Automatically modify real projects
- Automatically generate full Project Profiles from source code
- Replace human review
- Grant file-system permissions to Codex or any other agent

Automatic extraction, drift detection, and controlled write workflows are planned for later versions.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-account>/modeskill.git
cd modeskill
```

If you want Codex to recognize Modeskill as a user-level Skill, create a symbolic link:

```bash
mkdir -p ~/.agents/skills

ln -s \
  /path/to/modeskill/.agents/skills/modeskill \
  ~/.agents/skills/modeskill
```

After this, Codex can load Modeskill when you explicitly call:

```text
$modeskill
```

If you are using another coding agent or IDE, you can still use Modeskill by asking the agent to read:

```text
.agents/skills/modeskill/SKILL.md
```

and follow the relevant module instructions.

---

## Start the local settings UI

Run:

```bash
python3 .agents/skills/modeskill/configurator/server.py
```

Then open:

```text
http://127.0.0.1:8765/
```

The settings page runs locally only.

It listens on `127.0.0.1` or `localhost`.

It is not a hosted web application and is not exposed to the public internet.

To stop the server, return to the terminal and press:

```text
Control + C
```

---

## How to configure a workspace

Open the settings page and follow these steps:

1. Enter a Workspace name.
2. Enter the local Workspace root folder.
3. Configure discovery depth, project markers, include rules, and exclude rules.
4. Add manual project paths if some projects cannot be discovered automatically.
5. Click **Rediscover projects**.
6. Select:
   - Primary reference project
   - Secondary reference projects
   - Target project
7. Select the UI dimensions to analyze.
8. Validate and save the configuration.

Workspace configuration is stored locally in:

```text
.local/workspaces/
```

This folder is ignored by Git.

---

## Important security model

Modeskill separates three concepts.

### 1. Configuration permission

The settings UI defines which local workspace Modeskill is allowed to reason about.

This does not automatically grant file-system access to Codex or any other agent.

### 2. Runtime access

The coding agent must still be able to read the configured local folders in its actual runtime environment.

If the configured workspace is not accessible, Modeskill should report that clearly instead of guessing.

### 3. Write authorization

Reference projects are always read-only.

The target project is read-only by default.

A future write-capable workflow must require:

- Target write policy allowing explicit per-task authorization
- The user clearly authorizing write access in the current task
- The target path still being inside the configured target project
- The runtime environment actually having write permission

A configuration option must never be treated as current write authorization.

---

## Module distribution

Modeskill supports two module distribution modes.

### Synced with repository

Git-synced modules live inside:

```text
.agents/skills/modeskill/
```

These modules can be tracked by Git and shared with other users.

The current Git-synced module is:

```text
ui-consistency
```

### Local only

Local-only modules live inside:

```text
.local/modules/
```

They are ignored by Git and will not be uploaded to GitHub.

They are intended for private workflows, personal preferences, or machine-specific configuration.

If another user clones this repository, they will not receive your local-only modules or workspace configuration.

---

## Using Modeskill with Codex

### Check whether Modeskill is available

```text
Use $modeskill and read the current workspace configuration.

Run in read-only mode.
Do not modify any files.

Tell me:
1. Whether Modeskill loaded successfully.
2. Whether the workspace configuration was found.
3. Which projects are configured as primary reference, secondary references, and target.
4. Whether any local-only modules are installed and enabled.
5. Whether write access is currently authorized.
```

### Run a read-only UI consistency analysis

```text
Use $modeskill to run a read-only UI consistency analysis.

Use the configured primary reference, secondary references, and target project.

Requirements:
1. Do not modify any files.
2. Do not create or update Project Profile files.
3. Read only the source files needed for evidence.
4. Cite file evidence for each conclusion.
5. Classify conclusions as inherited, adapted, project-specific, unresolved, or deprecated.
6. Do not treat a single accidental CSS value as a global rule.
7. List which files would likely be affected if a future refinement is implemented.

Do not perform the refinement.
```

### Use Modeskill from another coding agent

If the agent does not support `$modeskill`, ask it to read:

```text
.agents/skills/modeskill/SKILL.md
```

Example:

```text
Read .agents/skills/modeskill/SKILL.md and follow the ui-consistency module.

Run a read-only UI consistency analysis using:
- Primary reference: <reference-project>
- Secondary references: <secondary-projects>
- Target project: <target-project>

Do not modify any files.
Each conclusion must include evidence.
```

---

## Validation

Run the built-in checks:

```bash
python3 .agents/skills/modeskill/shared/scripts/validate_config.py
python3 .agents/skills/modeskill/ui-consistency/scripts/validate_profile.py
python3 .agents/skills/modeskill/ui-consistency/scripts/validate_report.py
python3 scripts/validate_modeskill.py
python3 -m unittest discover -s tests
```

The built-in schema validator only implements the subset of JSON Schema Draft 2020-12 keywords used by Modeskill v0.1. It is not a complete JSON Schema implementation.

---

## Local files and backup

These folders are intentionally ignored by Git:

```text
.local/workspaces/
.local/modules/
```

They may contain:

- Local workspace paths
- Local module registry
- Machine-specific settings
- Local-only module content

They will not be restored by `git clone` or `git pull`.

Before deleting your local Modeskill folder, manually back up:

```text
.local/workspaces/
.local/modules/
```

---

## Repository safety

Modeskill is designed to avoid leaking private local project content.

The public repository should not include:

- `.local`
- API keys
- tokens
- cookies
- passwords
- production `.env` files
- real workspace configuration
- private local-only modules
- business project source code

Example projects under `examples/` are synthetic and are only used for validation.

---

## Current status

Modeskill is currently at v0.1.

The project is usable as a local configuration and consistency-analysis framework, but it is still early-stage.

Recommended use today:

- Configure a workspace
- Discover projects
- Select references and target
- Run read-only UI consistency analysis
- Review evidence and recommendations manually
- Only perform code changes after a separate explicit task

---

## License

MIT License

Copyright (c) 2026 jonsungo

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

<sub>
中文说明：Modeskill 是一个面向 Coding Agent 的本地优先 Skill，用来帮助多个相关项目保持 UI、组件和交互逻辑的一致性。它不是一个固定的 CSS 模板，也不是完整设计系统包，而是一套让 Agent 从参考项目中提取证据、判断目标项目应当继承、适配或保留差异的方法。
</sub>

<br />

<sub>
当前 v0.1 主要提供 Workspace 配置、项目发现、UI 一致性分析方法、Schema、验证脚本和本地设置界面。它可以帮助用户指定主要参考项目、辅助参考项目和目标项目，并在只读模式下生成一致性分析思路。v0.1 还不会自动扫描完整真实项目、自动监测样式漂移或自动修改业务代码。
</sub>

<br />

<sub>
使用方式：先启动本地设置页，配置 Workspace root、参考项目和目标项目；然后在 Codex 中调用 $modeskill，要求它进行只读 UI 一致性分析。参考项目永远只读，目标项目默认只读。任何未来写入都必须由用户在当前任务中明确授权。
</sub>

<br />

<sub>
.local 目录不会进入 Git，也不会随 GitHub 同步。它用于保存本机 Workspace 配置、本机模块和机器相关设置。其他用户 clone 本仓库后，不会看到你的本机配置、本机模块或真实项目路径。
</sub>
