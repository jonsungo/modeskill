# Evidence Model

Every conclusion needs structured evidence from an authorized path.

Evidence records include a source file, locator, evidence type, confidence, classification, and whether the user explicitly designated the source as authoritative. Stable locator types are `line`, `selector`, `component`, `token`, `symbol`, `section`, and `other`.

Source authority order:

1. User-designated authoritative source.
2. Explicit Design Token.
3. Shared component.
4. Consistent implementation across projects.
5. Frequently repeated implementation.
6. Agent inference.

Agent inference must be marked `inferred` and must not be presented as an established convention. A single incidental value is not a global rule.
