# Authorization Model

Modeskill separates three independent permission layers.

1. **Configuration authorization** defines the Workspace root that Modeskill may read and whether the target may request `explicit-per-task` writing.
2. **Runtime environment permission** determines whether Codex and the operating system can actually read or write a resolved path.
3. **Current-task authorization** is the user's explicit instruction in the current task. It is never stored, inferred, or reused.

## Decisions

- Workspace root: read and discovery only.
- Primary and secondary references: always read-only; configuration and task instructions cannot make them writable.
- Target: read-only unless the policy is `explicit-per-task`, the current task explicitly authorizes writing, and the runtime environment can write the exact target path.
- Other discovered or manual projects: read-only.
- `discovered_projects`: cache only. Presence in the cache does not authorize writing.
- Configurator: cannot create, cache, or simulate current-task authorization.

Any failed condition returns a denial with the failed layer identified.
