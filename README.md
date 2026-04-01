# ATDD BMAD Template

A decoupled, behavior-driven test repository for acceptance, API, integration, and prompt evaluation testing. Designed to be fed story specs from a separate codebase — one spec produces implementation code in the code repo, and BDD test artifacts in this repo.

**[Living Documentation](https://agentifyhq.github.io/atdd-bmad-template/)** — Feature specifications with test results, auto-deployed to GitHub Pages.

## Architecture

```
Story Spec (.md)
      │
      ├──► Code Repo  →  implements the feature
      │
      └──► This Repo  →  generates BDD feature files + step definitions
                          across all test layers including prompt evaluation
```

**Four test layers, all BDD, unified living documentation:**

| Layer | Tool | Browser? | Purpose |
|-------|------|----------|---------|
| UI Acceptance | playwright-bdd | Yes | User journey validation |
| API | playwright-bdd | No | Service contract & business logic |
| Integration | playwright-bdd | No | Cross-service consistency |
| Prompt Eval (TS) | playwright-bdd + promptfoo API | No | LLM quality gates (deterministic, semantic, LLM-as-judge) |
| Prompt Eval (Python) | pytest-bdd + DeepEval + Ragas | No | Faithfulness, hallucination, RAG metrics |

Every layer uses **Gherkin feature files** as the single source of truth. Feature files define *what* quality means; step definitions define *how* to measure it.

## Quick Start

### Prerequisites

- Node.js >= 20
- Python >= 3.11 (for DeepEval/Ragas prompt evaluation + living docs)
- A running target application (for acceptance/API/integration tests)

### Setup

```bash
# TypeScript dependencies
npm install
npx playwright install

# Python dependencies (prompt evaluation + living docs)
cd tests/prompt-eval/python
pip install -e ".[docs]"
cd ../../..

# Environment — single .env file for all runners
cp .env.example .env
# Edit .env with your target URLs and API keys
```

### Environment Variables

All runners load from a single `.env` file in the project root:

- **Playwright (TS)** — loaded via `dotenv/config` in `playwright.config.ts`
- **pytest-bdd (Python)** — loaded via `python-dotenv` in `conftest.py`
- **promptfoo CLI** — auto-loads `.env`

| Variable | Required For | Example |
|----------|-------------|---------|
| `APP_URL` | Acceptance tests | `http://localhost:3000` |
| `API_URL` | API tests | `http://localhost:3000` |
| `USER_SERVICE_URL` | Integration tests | `http://localhost:3001` |
| `OPENAI_API_KEY` | `@semantic`, `@llm-judge`, `@rag` tests | `sk-...` |
| `ANTHROPIC_API_KEY` | `@llm-judge`, `@faithfulness` tests | `sk-ant-...` |

`@deterministic` tests run without any API keys.

### Running Tests

```bash
# All BDD tests (acceptance + API + integration + prompt-eval)
npm test

# By layer
npm run test:acceptance          # UI acceptance (browser)
npm run test:api                 # API tests (no browser)
npm run test:integration         # Multi-service integration
npm run test:prompt-eval         # Prompt eval — TS/promptfoo (no browser)
npm run test:prompt-eval:python  # Prompt eval — Python/DeepEval/Ragas
npm run test:prompt-eval:all     # Both prompt eval layers

# Exploratory (not BDD — standalone tooling)
npm run prompt:compare           # Side-by-side prompt/model comparison
npm run prompt:compare:view      # View comparison in browser UI
npm run prompt:redteam           # Security red-teaming
```

### Reports & Living Documentation

```bash
# Test reports
npm run report                   # Playwright HTML report (reports/playwright/)
npm run report:cucumber          # Cucumber report (reports/cucumber/)

# Living documentation site
npm run docs:serve               # Build + serve locally at http://127.0.0.1:8000
npm run docs:deploy              # Build + deploy to GitHub Pages
```

All test output is consolidated under `reports/` (gitignored).
Living docs site tooling lives in `spec-web/`.

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design, layer responsibilities, and decisions |
| [BDD Guide](docs/bdd-guide.md) | Writing feature files, step definitions, and tagging strategy |
| [Prompt Evaluation Guide](docs/prompt-eval-guide.md) | BDD prompt eval, promptfoo, DeepEval, Ragas |
| [CI/CD Integration](docs/ci-integration.md) | Pipeline setup and quality gates |

## Project Structure

```
features/                              # Gherkin feature files (the WHAT)
├── acceptance/                        # UI acceptance scenarios
├── api/                               # API contract scenarios
├── integration/                       # Cross-service scenarios
└── prompt-eval/                       # Prompt quality specifications
    ├── summarization/                 #   Output quality criteria
    ├── rag/                           #   RAG pipeline quality criteria
    └── safety/                        #   Safety guardrail criteria

tests/                                 # Step definitions (the HOW)
├── acceptance/steps/                  # UI steps (page + request)
├── api/steps/                         # API steps (request only)
├── integration/steps/                 # Multi-service steps
└── prompt-eval/
    ├── ts-steps/                      # TS — promptfoo API (playwright-bdd)
    ├── python/                        # Python — DeepEval + Ragas (pytest-bdd)
    └── promptfoo/                     # Standalone: comparison & red-teaming
        ├── prompts/                   #   Prompt templates (shared)
        └── datasets/                  #   Test data (shared across TS & Python)

support/                               # Shared test infrastructure
├── fixtures/                          # Composable Playwright fixtures
├── helpers/                           # Schema validators, utilities
└── factories/                         # Test data factories

spec-web/                              # Living documentation site
├── mkdocs.yml                         # MkDocs Material configuration
├── build-living-docs.py               # Generates pages from features + results
└── overrides/stylesheets/             # Custom CSS

reports/                               # All generated output (gitignored)
├── .features-gen/                     # BDD → Playwright test files
├── cucumber/                          # Cucumber HTML + JSON
├── playwright/                        # Playwright HTML report
└── test-results/                      # Screenshots, traces, videos
```

## Key Principle: What vs How

```
Feature File (WHAT)                    Step Definition (HOW)
─────────────────────                  ─────────────────────
"the output should be faithful"   →    DeepEval FaithfulnessMetric >= 0.7
"the output should pass rubric"   →    promptfoo matchesLlmRubric()
"the response status should be"   →    Playwright request.status()
"I should see a welcome message"  →    page.getByText().toBeVisible()
```

Feature files are stakeholder-readable specifications. Step definitions are engineering implementations. The same feature file can be executed by different runners (playwright-bdd for TS, pytest-bdd for Python).
