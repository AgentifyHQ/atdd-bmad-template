# Convention: Test Organization

## Directory Structure

```
features/                              # WHAT — Gherkin specifications
├── acceptance/{domain}/{story}.feature
├── api/{domain}/{resource}.feature
├── integration/{flow}/{scenario}.feature
└── prompt-eval/
    ├── summarization/{quality-aspect}.feature
    ├── rag/{quality-aspect}.feature
    └── safety/{guardrail}.feature

tests/                                 # HOW — Step definitions
├── acceptance/steps/{domain}.steps.ts
├── api/steps/common-api.steps.ts      # Shared API steps (HTTP verbs, status)
├── api/steps/{domain}.steps.ts        # Domain-specific API steps
├── integration/steps/{flow}.steps.ts
└── prompt-eval/
    ├── ts-steps/prompt-eval.steps.ts  # TS: promptfoo assertions API
    ├── python/test_deepeval_*.py      # Python: DeepEval pytest-bdd steps
    ├── python/test_ragas_*.py         # Python: Ragas pytest-bdd steps
    └── promptfoo/                     # Standalone: comparison + red-teaming
        ├── prompts/{name}.txt         # Prompt templates (shared)
        ├── datasets/{name}.txt        # Test data (shared across TS + Python)
        └── promptfooconfig.yaml

support/                               # Shared infrastructure
├── fixtures/{concern}.fixtures.ts     # Playwright fixtures (one concern each)
├── helpers/{utility}.ts               # Pure functions (framework-agnostic)
└── factories/{entity}.factory.ts      # Test data factories

spec-web/                              # Living documentation site
├── mkdocs.yml                         # MkDocs Material config
├── build-living-docs.py               # Generates .md from features + results
├── overrides/stylesheets/             # Custom CSS
├── site/                              # Generated markdown (gitignored)
└── build/                             # Built HTML (gitignored)

reports/                               # All generated output (gitignored)
├── .features-gen/                     # BDD → Playwright test files
├── cucumber/                          # Cucumber HTML + JSON
├── playwright/                        # Playwright HTML report
└── test-results/                      # Screenshots, traces, videos
```

## Naming Rules

### Feature Files
- Location: `features/{layer}/{domain}/{descriptive-name}.feature`
- Name: kebab-case, describes the behavior being specified
- Examples: `user-login.feature`, `user-crud.feature`, `summarization-quality.feature`

### Step Definition Files
- Location: `tests/{layer}/steps/{name}.steps.ts` or `tests/prompt-eval/python/test_{name}.py`
- TS files: `{domain}.steps.ts` or `common-{layer}.steps.ts` for shared steps
- Python files: `test_{tool}_{domain}.py` (pytest requires `test_` prefix)

### Fixtures
- Location: `support/fixtures/{concern}.fixtures.ts`
- One fixture per concern: `api.fixtures.ts`, `base.fixtures.ts`
- Compose via `mergeTests` — never inheritance

### Factories
- Location: `support/factories/{entity}.factory.ts`
- Exports: `create{Entity}()` function with override pattern
- Always generate unique data (timestamps, counters) for parallel safety

### Datasets (Prompt Eval)
- Location: `tests/prompt-eval/promptfoo/datasets/`
- Articles: `article-{topic}.txt`
- Golden answers: `golden-summary-{topic}.txt` (matches article name)
- Shared by both TS and Python — single source of truth

### Prompts
- Location: `tests/prompt-eval/promptfoo/prompts/`
- Name: `{purpose}-v{version}.txt` (e.g., `summarize-v1.txt`)
- Use `{{variable}}` for template parameters

## Where New Files Go

| I need to... | Create file in... |
|-------------|-------------------|
| Add a new UI acceptance test | `features/acceptance/{domain}/{story}.feature` + `tests/acceptance/steps/{domain}.steps.ts` |
| Add a new API test | `features/api/{domain}/{resource}.feature` + reuse `common-api.steps.ts` or add domain-specific steps |
| Add a new integration test | `features/integration/{flow}/{scenario}.feature` + `tests/integration/steps/{flow}.steps.ts` |
| Add a new prompt quality spec | `features/prompt-eval/{category}/{aspect}.feature` + add steps to `ts-steps/` and/or `python/` |
| Add a new prompt template | `tests/prompt-eval/promptfoo/prompts/{name}-v{n}.txt` |
| Add a new test dataset | `tests/prompt-eval/promptfoo/datasets/{name}.txt` |
| Add a reusable fixture | `support/fixtures/{concern}.fixtures.ts` |
| Add a data factory | `support/factories/{entity}.factory.ts` |
| Add a helper function | `support/helpers/{utility}.ts` |

## What NOT to Create

- No `test_*.ts` files outside of step definitions — all tests are BDD
- No Page Object classes — use fixtures + pure functions
- No `utils/` or `lib/` directories — use `support/helpers/`
- No test data inside step definitions — use factories or datasets
- No duplicate datasets — both TS and Python read from the same `datasets/` directory

## Generated Files (gitignored)

All generated/transient output lives under `reports/`:

- `reports/.features-gen/` — Auto-generated Playwright test files from BDD
- `reports/cucumber/` — Cucumber HTML + JSON reports
- `reports/playwright/` — Playwright HTML report
- `reports/test-results/` — Test artifacts (screenshots, traces)

Living docs site output lives under `spec-web/`:

- `spec-web/site/` — Generated markdown pages (input to mkdocs)
- `spec-web/build/` — Built static HTML site (output of mkdocs)
