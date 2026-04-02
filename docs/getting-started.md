# Getting Started

## Prerequisites

- Node.js >= 20
- Python >= 3.11 (for DeepEval/Ragas prompt evaluation + living docs)
- A running target application (for acceptance/API/integration tests)

## Setup

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

## Environment Variables

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

## Running Tests

```bash
# All BDD tests (excludes @example template tests)
npm test

# By layer
npm run test:acceptance          # UI acceptance (browser)
npm run test:api                 # API tests (no browser)
npm run test:integration         # Multi-service integration
npm run test:prompt-eval         # Prompt eval — TS/promptfoo (no browser)
npm run test:prompt-eval:python  # Prompt eval — Python/DeepEval/Ragas
npm run test:prompt-eval:all     # Both prompt eval layers

# Template examples only
npm run test:examples            # Run @example tests (template demos)

# Exploratory (not BDD — standalone tooling)
npm run prompt:compare           # Side-by-side prompt/model comparison
npm run prompt:compare:view      # View comparison in browser UI
npm run prompt:redteam           # Security red-teaming
```

## Reports & Living Documentation

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

> After deploying, GitHub Pages CDN may serve cached pages for a few minutes.
> Use **Cmd+Shift+R** (Mac) or **Ctrl+Shift+R** (Windows/Linux) to hard refresh.

## Playwright Configuration

Key settings in `playwright.config.ts`:

| Setting | Default | Options |
|---------|---------|---------|
| `screenshot` | `'only-on-failure'` | `'on'` (every test), `'only-on-failure'`, `'off'` |
| `trace` | `'on-first-retry'` | `'on'` (every test), `'on-first-retry'`, `'off'` |
| `video` | `'off'` | `'on'` (every test), `'on-first-retry'`, `'off'` |

Screenshots, traces, and videos are saved to `reports/test-results/`. To change, edit the `use` block in `playwright.config.ts`:

```typescript
use: {
  screenshot: 'only-on-failure',  // captures screenshot when a test fails
  trace: 'on-first-retry',        // captures trace on retry (open with: npx playwright show-trace)
  video: 'off',                   // set to 'on-first-retry' to record video of failures
}
```

## Design References

Drop Figma exports or mockup images into an `assets/` folder next to feature files:

```
features/acceptance/user-management/
├── user-login.feature
├── user-login-visual.feature
└── assets/                          ← Figma exports go here
    ├── login-page.png
    ├── login-error-state.png
    └── dashboard.png
```

Images automatically appear as a scrollable gallery on the feature's living docs page. Click any image to view full-size.

## Visual Regression

Tag acceptance scenarios with `@visual` for screenshot-based testing:

```gherkin
@acceptance @visual
Scenario: Login page matches visual baseline
  Given I am on the login page
  Then the page should match the visual baseline "login-page"
```

Visual diffs are viewable in the Playwright HTML report (`npm run report`) with an interactive slider. Update baselines after intentional changes:

```bash
npx playwright test --update-snapshots --grep @visual
```
