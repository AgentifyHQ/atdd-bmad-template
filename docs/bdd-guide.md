# BDD Guide

## Writing Feature Files

Feature files are the heart of this repo. They serve triple duty:

1. **Specification** — human-readable acceptance criteria
2. **Executable test** — automated via step definitions
3. **Living documentation** — generated via Cucumber reporter

### File Organization

```
features/
├── acceptance/           # UI journeys (browser-based)
│   └── {domain}/
│       └── {story}.feature
├── api/                  # API contracts (no browser)
│   └── {domain}/
│       └── {resource}.feature
├── integration/          # Cross-service flows (no browser)
│   └── {flow-name}/
│       └── {scenario-group}.feature
└── prompt-eval/          # LLM quality specifications (no browser)
    ├── summarization/    #   Output quality criteria
    ├── rag/              #   RAG pipeline quality criteria
    └── safety/           #   Safety guardrail criteria
```

Organize by **domain** (user-management, orders, billing), not by test type. The directory under `features/` determines which Playwright project runs it.

Prompt eval feature files are shared between two runners:
- **playwright-bdd** (TypeScript) — deterministic, semantic, LLM-as-judge via promptfoo
- **pytest-bdd** (Python) — faithfulness, RAG metrics via DeepEval/Ragas

### Feature File Template

```gherkin
@api @P0
Feature: {Resource} {Operation}
  As a {role/persona}
  I want to {action}
  So that {business value}

  Background:
    Given {common precondition for all scenarios}

  @smoke
  Scenario: {Happy path description}
    Given {specific precondition}
    When {action taken}
    Then {expected outcome}
    And {additional assertion}

  @negative
  Scenario: {Error case description}
    When {invalid action}
    Then the response status should be {error code}
    And the response error code should be "{ERROR_CODE}"

  Scenario Outline: {Parameterized scenario}
    When {action with "<param>"}
    Then {outcome with "<expected>"}

    Examples:
      | param   | expected |
      | value1  | result1  |
      | value2  | result2  |
```

### Tagging Strategy

Tags control execution, filtering, and reporting:

| Tag | Purpose | Usage |
|-----|---------|-------|
| `@acceptance` | UI acceptance tests | Auto-applied by project |
| `@api` | API tests | Auto-applied by project |
| `@integration` | Integration tests | Auto-applied by project |
| `@prompt-eval` | Prompt evaluation tests | Auto-applied by project |
| `@P0` | Critical priority | Must pass for release |
| `@P1` | High priority | Should pass for release |
| `@P2` | Medium priority | Nice to have |
| `@smoke` | Smoke test subset | Quick sanity check |
| `@negative` | Error/edge cases | Negative testing |
| `@eventual-consistency` | Async assertions | Polling-based verification |
| `@deterministic` | Free, fast checks | Word count, contains, format |
| `@semantic` | Embedding similarity | Regression vs golden answers |
| `@llm-judge` | LLM-as-judge evaluation | Quality rubrics, factuality |
| `@faithfulness` | Grounding checks | DeepEval/Ragas faithfulness |
| `@rag` | RAG pipeline metrics | Context precision, recall |
| `@safety` | Safety guardrails | Banned patterns, prompt injection |
| `@wip` | Work in progress | Exclude from CI |

Run with tag filters:

```bash
# Only smoke tests
npx playwright test --project=api --grep "@smoke"

# Exclude WIP
npx playwright test --grep-invert "@wip"
```

---

## Writing Step Definitions

### For UI Acceptance Tests (browser)

Step definitions use `page` for browser interaction and `request` for API data seeding:

```typescript
import { createBdd } from 'playwright-bdd';

const { Given, When, Then } = createBdd();

// Seed data via API (fast), interact via browser (realistic)
Given('a user exists with email {string}', async ({ request }, email: string) => {
  await request.post('/api/test/seed-user', {
    data: { email, password: 'TestPass123!' },
  });
});

When('I click the submit button', async ({ page }) => {
  await page.getByRole('button', { name: /submit/i }).click();
});

Then('I should see {string}', async ({ page }, text: string) => {
  await expect(page.getByText(text)).toBeVisible();
});
```

### For API Tests (no browser)

Step definitions use only `request` — no `page` fixture:

```typescript
import { createBdd } from 'playwright-bdd';

const { When, Then } = createBdd();

When('I send a GET request to {string}', async ({ request }, path: string) => {
  // Store response for Then assertions
  const response = await request.get(path);
  // ... store in context
});

Then('the response status should be {int}', async ({}, status: number) => {
  // Assert against stored response
  expect(ctx.lastResponse.status).toBe(status);
});
```

### For Integration Tests (multi-service)

Step definitions target different services via environment-configured URLs:

```typescript
Given('the user service is available at USER_SERVICE_URL', async ({}) => {
  ctx.serviceUrls.user = process.env.USER_SERVICE_URL || 'http://localhost:3001';
});

When('I create an order for user', async ({ request }) => {
  const response = await request.post(`${ctx.serviceUrls.order}/api/orders`, {
    data: { userId: ctx.userId, items: [...] },
  });
});

// Polling for eventual consistency
Then('eventually the inventory should be {int} units', async ({ request }, expected: number) => {
  for (let attempt = 0; attempt < 15; attempt++) {
    const resp = await request.get(`${ctx.serviceUrls.inventory}/api/inventory/${id}`);
    const body = await resp.json();
    if (body.quantity === expected) return;
    await new Promise(r => setTimeout(r, 1000));
  }
  // Final assertion with clear failure message
});
```

### For Prompt Evaluation — TypeScript (playwright-bdd + promptfoo)

Step definitions use promptfoo's programmatic assertion API — no browser, no `page`:

```typescript
import { assertions } from 'promptfoo';
const { matchesSimilarity, matchesLlmRubric, matchesFactuality } = assertions;

Given('the source article {string}', async ({}, filename: string, testInfo) => {
  const ctx = getCtx(testInfo.testId);
  ctx.sourceArticle = loadDataset(filename);
});

When('I generate a summary using prompt {string}', async ({ request }, promptId: string, testInfo) => {
  const ctx = getCtx(testInfo.testId);
  // Call LLM via API, store output
  ctx.generatedOutput = await callLLM(request, ctx.sourceArticle, promptId);
});

// Deterministic
Then('the output should be under {int} words', async ({}, max: number, testInfo) => {
  const ctx = getCtx(testInfo.testId);
  expect(ctx.generatedOutput.split(/\s+/).length).toBeLessThanOrEqual(max);
});

// Semantic similarity (promptfoo embeddings)
Then('the output should be semantically similar to the golden answer with threshold {float}',
  async ({}, threshold: number, testInfo) => {
    const ctx = getCtx(testInfo.testId);
    const result = await matchesSimilarity(ctx.generatedOutput, ctx.goldenAnswer, threshold);
    expect(result.pass).toBe(true);
  },
);

// LLM-as-judge (promptfoo rubric)
Then('the output should pass the rubric:', async ({}, rubric: string, testInfo) => {
  const ctx = getCtx(testInfo.testId);
  const result = await matchesLlmRubric(rubric.trim(), ctx.generatedOutput, {});
  expect(result.pass).toBe(true);
});
```

### For Prompt Evaluation — Python (pytest-bdd + DeepEval/Ragas)

The **same feature files** are executed by pytest-bdd with Python step definitions:

```python
from pytest_bdd import scenarios, given, when, then, parsers
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

# Load shared feature files
scenarios("summarization/summarization-quality.feature")

@given(parsers.parse('the source article "{filename}"'), target_fixture="eval_context")
def load_article(filename, datasets_dir, eval_context):
    eval_context["source_article"] = (datasets_dir / filename).read_text()
    return eval_context

@then(parsers.parse('the output should be factual given "{claim}"'))
def check_factuality(claim, eval_context):
    test_case = LLMTestCase(
        input="Summarize this article",
        actual_output=eval_context["generated_output"],
        retrieval_context=[eval_context["source_article"]],
    )
    assert_test(test_case, [FaithfulnessMetric(threshold=0.7)])
```

### For RAG Quality — Python (pytest-bdd + Ragas)

RAG-specific feature files use Ragas metrics in step definitions:

```python
from ragas import evaluate
from ragas.metrics import Faithfulness, ResponseRelevancy

@then(parsers.parse("the faithfulness score should be >= {threshold:f}"))
def check_faithfulness(threshold, rag_context):
    dataset = EvaluationDataset(samples=[build_sample(rag_context)])
    result = evaluate(dataset=dataset, metrics=[Faithfulness()])
    score = result.scores[0]["faithfulness"]
    assert score >= threshold
```

---

## Step Definition Patterns

### Sharing State Within a Scenario

Steps within a scenario share state through a context object keyed by test ID:

```typescript
type ApiContext = {
  lastResponse: { status: number; body: any };
  createdEntities: Map<string, any>;
};

const contexts = new Map<string, ApiContext>();

function getCtx(testId: string): ApiContext {
  if (!contexts.has(testId)) {
    contexts.set(testId, { lastResponse: { status: 0, body: null }, createdEntities: new Map() });
  }
  return contexts.get(testId)!;
}
```

### Reusable Steps

Common steps (HTTP methods, status assertions) live in `common-api.steps.ts` and are shared across all API feature files. Domain-specific steps go in dedicated files.

### Path Parameter Resolution

Dynamic paths like `/api/users/{userId}` are resolved from the context:

```gherkin
Given a user exists with name "James" and email "james@test.com"
When I send a GET request to "/api/users/{userId}"
```

The `{userId}` is replaced with the ID stored during the Given step.

---

## Living Documentation

The Cucumber reporter generates HTML documentation from feature files:

```bash
# Generate and view
npm run test:api
npm run report:cucumber
```

The report shows:
- All features organized by domain
- Pass/fail status per scenario
- Scenario outlines with example data
- Tags and metadata
- Execution time per step

This is your **living documentation** — always current, always reflecting actual test results.
