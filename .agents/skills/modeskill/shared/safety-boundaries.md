# Safety Boundaries

## Repository Development Mode

- Only modify the current `modeskill` repository.
- Do not read or modify `../modetools`, Easy, Trans, or other real Modelab projects while developing this repository.
- Do not install a user-level Skill, dependencies, or perform Git staging, commits, or pushes unless the user separately requests them.

## Skill Runtime Mode

- Treat the configured Workspace root as a read-only discovery and analysis boundary.
- Access only paths whose resolved real path remains inside that root.
- Report an inaccessible Workspace root as an environment-permission error, not as an empty discovery result.
- Keep primary and secondary reference projects read-only in every circumstance.
- Keep the target read-only by default. A target write decision requires `explicit-per-task` policy, explicit authorization in the current task, and actual environment write access.
- Never reuse historical authorization or extend target authorization to another project.
- Treat the Configurator as configuration tooling only. It cannot grant operating-system access or current-task write authorization.

Project Profiles may be generated in memory. Store them under `.local/` by default; writing elsewhere requires a separately approved destination and must never write into a reference project.
