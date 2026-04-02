# Test Architect — Standalone ATDD Test Repository

This is a **decoupled BDD test repo** — it contains no application code. Tests validate behavior against running services. Story specs from a separate code repo produce feature files here.

## Golden Rule

**Feature files define WHAT. Step definitions define HOW. Never mix them.**

## Before You Write Code

Read the relevant convention file before making changes:

| Task | Read First |
|------|-----------|
| Adding/modifying feature files | [.claude/conventions/feature-file-standards.md](.claude/conventions/feature-file-standards.md) |
| Adding/modifying step definitions | [.claude/conventions/step-definition-patterns.md](.claude/conventions/step-definition-patterns.md) |
| Adding/modifying prompt evaluations | [.claude/conventions/prompt-eval-conventions.md](.claude/conventions/prompt-eval-conventions.md) |
| Understanding repo structure | [.claude/conventions/test-organization.md](.claude/conventions/test-organization.md) |

## Architecture at a Glance

Four BDD test layers, all driven by Gherkin feature files:

| Layer | Runner | Steps Location | Browser? |
|-------|--------|---------------|----------|
| UI Acceptance | playwright-bdd | `tests/acceptance/steps/` | Yes |
| API | playwright-bdd | `tests/api/steps/` | No |
| Integration | playwright-bdd | `tests/integration/steps/` | No |
| Prompt Eval (TS) | playwright-bdd + promptfoo API | `tests/prompt-eval/ts-steps/` | No |
| Prompt Eval (Python) | pytest-bdd + DeepEval + Ragas | `tests/prompt-eval/python/` | No |

Feature files live in `features/{layer}/` — never in `tests/`.

## Critical Rules

- **All test layers use BDD.** Every test starts as a `.feature` file. No raw test files without a corresponding feature.
- **Feature files are organized by domain**, not by test type. Example: `features/api/user-management/`, not `features/api/crud-tests/`.
- **Tags are mandatory.** Every feature file must have `@{layer}` and `@P{0-2}` tags.
- **No Page Object Model.** Use composable fixtures (`support/fixtures/`) and pure functions (`support/helpers/`).
- **API and integration tests never use browser.** They use Playwright's `request` fixture only.
- **Prompt eval feature files are shared** between playwright-bdd (TS) and pytest-bdd (Python). Both runners read from `features/prompt-eval/`.
- **promptfoo YAML is for comparison and red-teaming only**, not quality gates. Quality gates live in feature files.
- **Shared test data** lives in `tests/prompt-eval/promptfoo/datasets/`. Both TS and Python tests read from here.
- **Placeholders exist** in LLM generation steps. Replace with actual API calls before running against real services.
- **Every story needs `@github:owner/repo/issues/N` tag.** Links feature files to GitHub Issues. Created via `/create-story` skill.
- **Never create a feature file without a GitHub Issue**, and vice versa. They are an atomic pair.
- **Story status updates are automatic.** CI reads cucumber JSON, updates issue labels + project board. No manual intervention needed.

## Story Workflow

Use `/create-story` to create a new story. It generates:
1. GitHub Issue in **atdd-bmad-template** (body = story spec, labels: `story`, priority, epic)
2. Feature file (tagged `@github:AgentifyHQ/atdd-bmad-template/issues/{N}`)
3. Repo project board entry (auto-creates board if none exists)

**Epic label format:** `{source-repo}::{domain}::{layer-abbrev}` — e.g., `agent-hitl-gateway::interrupt-management::api`
- Layer abbreviations: `acceptance` → `acc`, `api` → `api`, `integration` → `int`, `prompt-eval` → `pe`

**Project boards** are per-repo (not org-level). Board is auto-created if missing.

After tests run, CI automatically:
- Labels issues `tests-passing` or `tests-failing`
- Moves project board column to "Done" or keeps "In Progress"

## Run Commands

```bash
npm run test:acceptance          # UI BDD
npm run test:api                 # API BDD
npm run test:integration         # Integration BDD
npm run test:prompt-eval         # Prompt eval BDD (TS/promptfoo)
npm run test:prompt-eval:python  # Prompt eval BDD (Python/DeepEval/Ragas)
npm run test:prompt-eval:all     # Both prompt eval runners
npm run prompt:compare           # Side-by-side prompt comparison (standalone)
npm run prompt:redteam           # Security red-teaming (standalone)
npm run report:cucumber          # Cucumber report (reports/cucumber/)
npm run docs:serve               # Living documentation site (spec-web/)
npm run docs:deploy              # Deploy to GitHub Pages
```

## Output Locations

- `reports/` — All test output (gitignored): cucumber, playwright, test-results, .features-gen
- `spec-web/` — Living documentation tooling: mkdocs config, build script, CSS overrides
- `spec-web/site/` + `spec-web/build/` — Generated docs (gitignored)
