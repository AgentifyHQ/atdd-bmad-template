# ATDD BMAD Template

A decoupled, behavior-driven test repository template for acceptance, API, integration, and prompt evaluation testing. Story specs from a separate codebase produce BDD feature files here.

**[Living Documentation](https://agentifyhq.github.io/atdd-bmad-template/)** — Feature specifications with test results, auto-deployed to GitHub Pages.

## Quick Start

```bash
npm install && npx playwright install
cp .env.example .env                   # Edit with your target URLs + API keys
npm test                               # Run all tests (excludes @example demos)
npm run test:examples                  # Run template example tests
npm run docs:serve                     # Living docs at http://127.0.0.1:8000
```

## Test Layers

| Layer | Tool | Purpose |
|-------|------|---------|
| UI Acceptance | playwright-bdd | User journey validation |
| API | playwright-bdd | Service contract & business logic |
| Integration | playwright-bdd | Cross-service consistency |
| Prompt Eval (TS) | playwright-bdd + promptfoo | LLM quality gates |
| Prompt Eval (Python) | pytest-bdd + DeepEval + Ragas | Faithfulness, RAG metrics |

All layers use Gherkin feature files as the single source of truth. Template examples are tagged `@example` and excluded from `npm test` by default.

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Setup, environment variables, running tests, reports |
| [Architecture](docs/architecture.md) | System design, layer responsibilities, and decisions |
| [Project Structure](docs/project-structure.md) | Directory layout and what-vs-how principle |
| [BDD Guide](docs/bdd-guide.md) | Writing feature files, step definitions, and tagging |
| [Prompt Evaluation Guide](docs/prompt-eval-guide.md) | BDD prompt eval, promptfoo, DeepEval, Ragas |
| [CI/CD Integration](docs/ci-integration.md) | Pipeline setup and quality gates |
| [Contract Testing (Pact)](docs/contract-testing.md) | Service-to-service contract testing — lives in code repos, not here |
