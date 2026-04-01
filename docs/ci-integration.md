# CI/CD Integration

Guide for integrating this test repo into your CI/CD pipeline with quality gates.

## Pipeline Architecture

```
PR Opened / Push
      │
      ├── Stage 1: Lint & Type Check (fast, always)
      │     ├── TypeScript type check
      │     └── Python linting
      │
      ├── Stage 2: API Tests (fast, no browser)
      │     └── npx playwright test --project=api
      │
      ├── Stage 3: Integration Tests (medium, no browser)
      │     └── npx playwright test --project=integration
      │
      ├── Stage 4: Acceptance Tests (slow, browser)
      │     └── npx playwright test --project=acceptance
      │
      ├── Stage 5: Prompt Evaluation BDD (on prompt changes)
      │     ├── npx playwright test --project=prompt-eval
      │     └── pytest (pytest-bdd + DeepEval + Ragas)
      │
      ├── Stage 5b: Prompt Comparison (optional, on prompt changes)
      │     └── npx promptfoo eval (side-by-side comparison)
      │
      └── Stage 6: Living Docs Publish
            └── Upload Cucumber reports as artifacts
```

## GitHub Actions Example

```yaml
name: Test Suite

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run typecheck

  api-tests:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:api
        env:
          API_URL: ${{ vars.API_URL }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: api-test-results
          path: |
            playwright-report/
            cucumber-report/

  integration-tests:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:integration
        env:
          USER_SERVICE_URL: ${{ vars.USER_SERVICE_URL }}
          ORDER_SERVICE_URL: ${{ vars.ORDER_SERVICE_URL }}
          INVENTORY_SERVICE_URL: ${{ vars.INVENTORY_SERVICE_URL }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: integration-test-results
          path: playwright-report/

  acceptance-tests:
    needs: [api-tests, integration-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: npm run test:acceptance
        env:
          APP_URL: ${{ vars.APP_URL }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: acceptance-test-results
          path: |
            playwright-report/
            cucumber-report/
            test-results/

  prompt-eval:
    needs: lint
    runs-on: ubuntu-latest
    if: contains(github.event.pull_request.labels.*.name, 'prompt-change')
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      # BDD prompt eval — TypeScript (playwright-bdd + promptfoo API)
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:prompt-eval
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      # BDD prompt eval — Python (pytest-bdd + DeepEval + Ragas)
      - run: pip install -e tests/prompt-eval/python
      - run: npm run test:prompt-eval:python
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      # Upload living docs
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: prompt-eval-results
          path: cucumber-report/

      # promptfoo PR comment (optional)
      - uses: promptfoo/promptfoo-action@v1
        with:
          config: tests/prompt-eval/promptfoo/promptfooconfig.yaml
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Quality Gates

### Gate Definitions

| Gate | Condition | Blocks |
|------|-----------|--------|
| **API Contract** | All `@P0` API scenarios pass | Merge |
| **Integration Health** | All `@smoke` integration scenarios pass | Merge |
| **Acceptance Smoke** | All `@smoke @acceptance` scenarios pass | Merge |
| **Prompt Deterministic** | All `@deterministic` prompt-eval scenarios pass | Merge (if prompt changed) |
| **Prompt Semantic** | All `@semantic` prompt-eval scenarios pass | Merge (if prompt changed) |
| **Prompt LLM Judge** | All `@llm-judge` prompt-eval scenarios pass | Merge (if prompt changed) |
| **RAG Faithfulness** | All `@faithfulness` Ragas scenarios pass (>= 0.7) | Merge (if RAG changed) |

### Running Selective Tests

```bash
# Only P0 (critical) tests
npx playwright test --grep "@P0"

# Only smoke tests across all projects
npx playwright test --grep "@smoke"

# Specific project + tag
npx playwright test --project=api --grep "@smoke"
```

## Parallelization

### Sharding (Large Suites)

```yaml
acceptance-tests:
  strategy:
    matrix:
      shard: [1/4, 2/4, 3/4, 4/4]
  steps:
    - run: npx playwright test --project=acceptance --shard=${{ matrix.shard }}
```

### Merge Shard Reports

```yaml
merge-reports:
  needs: acceptance-tests
  steps:
    - run: npx playwright merge-reports --reporter=html blob-report/
```

## Environment Configuration

### Secrets (GitHub)

| Secret | Used By |
|--------|---------|
| `ANTHROPIC_API_KEY` | promptfoo, DeepEval |
| `OPENAI_API_KEY` | DeepEval (judge model), Ragas |

### Variables (GitHub)

| Variable | Used By |
|----------|---------|
| `APP_URL` | Acceptance tests |
| `API_URL` | API tests |
| `USER_SERVICE_URL` | Integration tests |
| `ORDER_SERVICE_URL` | Integration tests |
| `INVENTORY_SERVICE_URL` | Integration tests |

## Living Documentation Deployment

Publish Cucumber reports as a static site for team visibility:

```yaml
publish-docs:
  needs: [api-tests, acceptance-tests]
  if: github.ref == 'refs/heads/main'
  steps:
    - uses: actions/download-artifact@v4
    - uses: peaceiris/actions-gh-pages@v4
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: cucumber-report/
```

This makes living documentation available at `https://{org}.github.io/{repo}/`.
