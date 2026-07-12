# Modeskill Safety Boundaries

## Repository development

- Only modify the current `modeskill` repository.
- Do not read or modify `../modetools`, Easy, Trans, or other real Modelab projects during v0.1 development.
- Do not install dependencies or a user-level Skill. Do not automatically stage, commit, or push.

## Skill runtime

Workspace configuration authorizes read-only discovery and analysis inside one resolved root. It does not grant Codex or the operating system access. If the runtime cannot read an existing configured root, Modeskill must report an environment-permission error rather than “no projects found.”

Primary and secondary references are permanently read-only. The target is read-only by default. Target writing requires all three conditions: configuration policy `explicit-per-task`, explicit authorization in the current task, and actual runtime write access to the current target. Authorization is not stored or reused and never covers another project.

The Configurator only edits configuration. It cannot grant runtime permissions, create current-task authorization, edit business projects, or run Git operations.

Git-synced modules live under the resolved Skill directory. Local-only modules live under the resolved repository root's `.local/modules`; resolve symlinks and reject paths outside that directory. The Configurator does not migrate modules or change Git history. Local modules and Workspace configuration are not backed up by Git.

Internal symbolic links are accepted only when their resolved targets remain inside the applicable allowed directory. Resolve and validate registry files, module metadata, entry references, Workspace storage, and final configuration files before reading or writing.

Project Profiles default to memory or `.local/`. Saving elsewhere requires an explicit destination, and references remain prohibited destinations.
