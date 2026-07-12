# Consistency Report Example

## Reference Sources

- `reference-project/index.html`
- `reference-project/app.js`
- `reference-project/src/styles/tokens.css`

## Project Profile Draft

The target inherits shared semantics, adapts its brand accent, and keeps a wider review dialog as a project-specific decision. Consistency does not mean visually identical output.

## Inherited Rules

- Typography uses the shared semantic type tokens.

## Adapted Rules

- Color semantics preserve role names with a target accent.

## Project-specific Rules

- The review dialog is wider for target workflow content.

## Unresolved Conflicts

- The simulated page set cannot establish a global breakpoint policy.

## Deprecated Patterns

- `.legacy-inline-form` is explicitly replaced and must not propagate.

## Implementation Recommendations

- Document approved target variations before any future implementation task.

## Files That Would Be Affected

- `target-project/src/styles/tokens.css`
- `target-project/src/components/Modal.css`

## Risk And Write Authorization

- Risk: low.
- Authorization: read-only.

## Known Limits

- v0.1 discovers projects and validates structured examples; it does not fully scan or automatically modify real projects.
