# Workspace Model

A Workspace is one user-authorized root containing one or more projects. A single Git repository may contain several projects.

## Authoritative Configuration

- Workspace name and root.
- Discovery rules, including recursion, depth, markers, include/exclude patterns, root-project handling, and continued scanning below repository roots.
- Manual project relative paths.
- Primary reference, secondary references, and target selections.
- Analysis and authorization settings.

## Discovery Cache

`discovered_projects` and `discovered_at` are replaceable scan output. Rediscovery replaces this cache. Role selections use normalized relative paths and must resolve to a currently discovered or manual project that still exists.

## Multi-project Repositories

- `treat_workspace_root_as_project` controls whether a marked Workspace root is listed as a project.
- `continue_below_repository_root` keeps scanning children after any `.git` or other project marker is found.
- `manual_projects` registers markerless HTML, CSS, JavaScript, PHP, or other projects.
- Automatic and manual projects are merged by normalized relative path and deduplicated.

The configured root is a Modeskill read boundary. It does not grant Codex or the operating system access and never grants write access.
