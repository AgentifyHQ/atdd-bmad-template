# Test Architect — Standalone ATDD Test Repository

This is a **decoupled BDD test repo** — it contains no application code. Tests validate behavior against running services. Story specs from a separate code repo produce feature files here.

## Golden Rule

**Feature files define WHAT. Step definitions define HOW. Never mix them.**

## Before You Take Action

Read the relevant convention file before making changes:

| Task | Read First |
|------|-----------|
| Adding/modifying feature files | [feature-file-standards.md](.claude/conventions/feature-file-standards.md) |
| Adding/modifying step definitions | [step-definition-patterns.md](.claude/conventions/step-definition-patterns.md) |
| Adding/modifying prompt evaluations | [prompt-eval-conventions.md](.claude/conventions/prompt-eval-conventions.md) |
| Understanding repo structure | [test-organization.md](.claude/conventions/test-organization.md) |
| Creating stories, managing epics/boards | [project-management.md](.claude/conventions/project-management.md) |

## Critical Rules

- **All test layers use BDD.** Every test starts as a `.feature` file.
- **Feature files are organized by domain**, not by test type.
- **Tags are mandatory.** Every feature file must have `@{layer}` and `@P{0-2}` tags.
- **No Page Object Model.** Use composable fixtures + pure functions.
- **API and integration tests never use browser.** `request` fixture only.
- **Never create a feature file without a GitHub Issue**, and vice versa. They are an atomic pair. Use `/create-story`.
- **`@example` features are template demos.** Excluded from `npm test` by default. Run with `npm run test:examples`.
