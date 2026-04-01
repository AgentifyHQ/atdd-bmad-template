# Architecture

## Design Principles

### 1. Tests are decoupled from implementation

This repo contains **no application code**. Tests validate behavior against running services via HTTP (API) or browser (UI). The story spec is the contract between the code repo and this test repo.

### 2. Feature files are the single source of truth

Every test layer — including prompt evaluation — uses Gherkin `.feature` files. These are:
- Human-readable specifications
- Executable tests
- Living documentation (via Cucumber reporter)

### 3. BDD separates What from How

Feature files define **what** quality means in stakeholder language. Step definitions define **how** to measure it using specific tools. This separation means:
- Product owners can read and approve quality criteria
- Engineers can swap evaluation tools without changing specs
- The same feature file can be executed by multiple runners

### 4. One framework per language, unified by Gherkin

- **TypeScript**: playwright-bdd (Playwright runner + Cucumber reporter)
- **Python**: pytest-bdd (pytest runner + DeepEval/Ragas metrics)
- **Shared**: Gherkin feature files in `features/` are the common contract

---

## Layer Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│               Feature Files (.feature) — The WHAT                │
│                  Living Documentation Source                      │
├──────────────┬──────────┬──────────────┬────────────────────────┤
│ Acceptance   │   API    │ Integration  │    Prompt Evaluation    │
│ (browser)    │(request) │  (request)   │ (LLM API calls)        │
├──────────────┼──────────┼──────────────┼────────────────────────┤
│ playwright-  │playwright│ playwright-  │ playwright-bdd         │
│ bdd + page   │-bdd +    │ bdd +        │ + promptfoo API        │
│              │ request  │ request +    │ ────────────────────── │
│              │          │ polling      │ pytest-bdd             │
│              │          │              │ + DeepEval + Ragas     │
├──────────────┴──────────┴──────────────┴────────────────────────┤
│     Playwright Test Runner          │    pytest Runner           │
│     Cucumber Reporter               │    pytest-bdd Reporter     │
└─────────────────────────────────────┴────────────────────────────┘

Standalone (not BDD):
┌──────────────────────────────────────┐
│ promptfoo YAML — Comparison & Red-team│
│ Side-by-side, security auditing       │
└──────────────────────────────────────┘
```

### Acceptance Tests (UI)

- **Purpose**: Validate critical user journeys end-to-end through the browser
- **Fixtures**: `page`, `request` (for API data seeding)
- **When to use**: Revenue-critical paths, visual workflows, multi-page journeys
- **Risk if skipped**: Users encounter broken flows in production

### API Tests

- **Purpose**: Validate service contracts, business logic, error handling
- **Fixtures**: `request` only (no browser overhead)
- **When to use**: CRUD operations, validation rules, auth, error codes
- **Risk if skipped**: Contract breaks go undetected, edge cases untested

### Integration Tests

- **Purpose**: Validate cross-service data flow and eventual consistency
- **Fixtures**: `request` with multi-service `baseUrl` targeting + polling
- **When to use**: Order flows spanning multiple services, async operations
- **Risk if skipped**: Services diverge silently, eventual consistency violations

### Prompt Evaluation (BDD)

- **Purpose**: Validate LLM output quality as stakeholder-readable specifications
- **Runners**: playwright-bdd (TS/promptfoo) + pytest-bdd (Python/DeepEval/Ragas)
- **Shared feature files**: Both runners read from `features/prompt-eval/`
- **When to use**: Any prompt change, model upgrade, RAG pipeline modification
- **Risk if skipped**: Prompt regression, hallucination, quality degradation

### Prompt Comparison & Red-Teaming (standalone)

- **Purpose**: Exploratory analysis, not specification
- **Tool**: promptfoo YAML config
- **When to use**: Comparing prompt versions, evaluating new models, security audits
- **Not BDD**: These are operational tools, not quality gate specifications

---

## Dual-Runner Architecture for Prompt Eval

The same `.feature` files are executed by two different BDD runners:

```
features/prompt-eval/summarization/summarization-quality.feature
      │
      ├──► playwright-bdd (TypeScript)
      │      Steps use: promptfoo assertions API
      │      Covers: deterministic, semantic similarity, LLM-as-judge
      │      Output: Cucumber HTML report (living docs)
      │
      └──► pytest-bdd (Python)
             Steps use: DeepEval metrics, Ragas metrics
             Covers: faithfulness, hallucination, RAG quality, custom rubrics
             Output: pytest report + optional Confident AI dashboard
```

This is intentional — each runner brings different strengths:

| Runner | Strength | Best For |
|--------|----------|----------|
| playwright-bdd + promptfoo | Semantic similarity (embeddings), factuality, red-team assertions | Regression testing, CI gates |
| pytest-bdd + DeepEval | 50+ research-backed metrics, agent eval | Deep quality analysis |
| pytest-bdd + Ragas | RAG-specific metrics (context precision, recall) | RAG pipeline validation |

Steps that overlap (e.g., deterministic checks) can exist in both runners. Steps that are tool-specific (e.g., Ragas context recall) only exist in the appropriate runner.

---

## Multi-Project Playwright Config

Each BDD layer is a separate Playwright project with its own `defineBddConfig`:

```typescript
const promptEvalTestDir = defineBddConfig({
  outputDir: '.features-gen/prompt-eval',
  features: 'features/prompt-eval/**/*.feature',
  steps: 'tests/prompt-eval/ts-steps/**/*.ts',
});
```

Projects run independently: `npx playwright test --project=prompt-eval`

---

## Fixture Composition

Fixtures follow the **pure function -> fixture wrapper** pattern:

1. **Pure functions** in `support/helpers/` — framework-agnostic, unit-testable
2. **Fixture wrappers** in `support/fixtures/` — inject Playwright context
3. **Composition** via `mergeTests` — combine capabilities without inheritance

---

## Data Flow

```
.env                              →  Service URLs, API keys
support/factories/                →  Test data generation
support/helpers/                  →  Schema validation (Zod)
support/fixtures/                 →  Playwright fixture composition
features/**/*.feature             →  Gherkin scenarios (shared BDD source)
tests/**/steps/*.ts               →  TS step definitions (playwright-bdd)
tests/prompt-eval/python/*.py     →  Python step definitions (pytest-bdd)
tests/prompt-eval/promptfoo/      →  Shared prompts, datasets, comparison config
.features-gen/                    →  Auto-generated Playwright test files (gitignored)
cucumber-report/                  →  Living documentation output (gitignored)
```

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| BDD for prompt evaluation | Quality criteria are stakeholder-readable specs, not just engineering metrics |
| Dual-runner (playwright-bdd + pytest-bdd) | Each ecosystem brings unique evaluation tools |
| Shared feature files | One spec, two execution backends — the "what" stays unified |
| promptfoo YAML for comparison only | Side-by-side comparison and red-teaming are exploratory, not BDD specs |
| Feature files for API/integration | Living documentation across all layers, not just UI |
| Zod for schema validation | Runtime validation + TypeScript types from one definition |
| No Page Object Model | Composable fixtures over inheritance chains |
