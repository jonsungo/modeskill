# Project Profile Specification

A Project Profile is an evidence-backed snapshot that may be generated in memory. Save it under `.local/` by default; never write it into a reference project without separate destination authorization.

It records project metadata, technology stack, sources, Design Tokens, typography, color semantics, spacing, components, interaction patterns, responsive behavior, engineering conventions, evidence, confidence, unresolved issues, and generation metadata.

Each conclusion should identify applicable source file, selector, component, token, stable locator, evidence type, confidence, classification, and whether the user explicitly designated the source. A locator may be `line`, `selector`, `component`, `token`, `symbol`, `section`, or `other`; line numbers are not mandatory.
