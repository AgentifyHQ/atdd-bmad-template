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

## Debugging Failures

When tests fail, use the `/probe-test-failures` skill in Claude Code to diagnose root causes. It opens the Playwright report and the live app side-by-side in Chrome, cross-references error messages with actual DOM state, and categorizes each failure as a test bug, app bug, environment issue, or flake.

```bash
# 1. Serve the Playwright report
npx playwright show-report reports/playwright --port 9323

# 2. Make sure the app under test is running

# 3. In Claude Code, run:
/probe-test-failures http://localhost:9323 http://localhost:3000
```

Requires the [Claude in Chrome](https://chromewebstore.google.com/detail/claude-in-chrome) MCP extension.

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Setup, environment variables, running tests, reports |
| [Architecture](docs/architecture.md) | System design, layer responsibilities, and decisions |
| [Project Structure](docs/project-structure.md) | Directory layout and what-vs-how principle |
| [BDD Guide](docs/bdd-guide.md) | Writing feature files, step definitions, and tagging |
| [Prompt Evaluation Guide](docs/prompt-eval-guide.md) | BDD prompt eval, promptfoo, DeepEval, Ragas |
| [CI/CD Integration](docs/ci-integration.md) | Pipeline setup and quality gates |
| [Testing Levels](docs/testing-levels.md) | Unit, integration, contract, E2E — what lives where and when to start |
| [Contract Testing (Pact)](docs/contract-testing.md) | Service-to-service contract testing — lives in code repos, not here |
