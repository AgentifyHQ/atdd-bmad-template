# Convention: Step Definition Patterns

## General Principles

1. **Steps are glue** — they connect Gherkin to framework APIs. Keep them thin.
2. **Business logic goes in helpers** (`support/helpers/`), not in steps.
3. **Data generation goes in factories** (`support/factories/`), not in steps.
4. **State is shared via context objects**, not global variables.

## TypeScript Steps (playwright-bdd)

### Imports

```typescript
import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';

const { Given, When, Then } = createBdd();
```

Always destructure `Given`, `When`, `Then` from `createBdd()` — not from `playwright-bdd` directly.

### Context Pattern (State Sharing)

Steps within a scenario share state through a Map keyed by `testInfo.testId`:

```typescript
type MyContext = {
  lastResponse: { status: number; body: any };
  createdEntities: Map<string, any>;
};

const contexts = new Map<string, MyContext>();

function getCtx(testId: string): MyContext {
  if (!contexts.has(testId)) {
    contexts.set(testId, {
      lastResponse: { status: 0, body: null },
      createdEntities: new Map(),
    });
  }
  return contexts.get(testId)!;
}
```

Access via `testInfo` parameter:

```typescript
When('I do something', async ({ request }, testInfo) => {
  const ctx = getCtx(testInfo.testId);
  // ... use and mutate ctx
});
```

### Fixture Access

Steps receive Playwright fixtures as the first argument:

```typescript
// UI steps — use `page` and `request`
Given('I am on the login page', async ({ page }) => { ... });

// API steps — use `request` only (no page, no browser)
When('I send a GET request to {string}', async ({ request }, path: string) => { ... });

// Prompt eval steps — use `request` for LLM API calls
When('I generate a summary', async ({ request }, testInfo) => { ... });
```

### Parameter Types

| Gherkin | TypeScript | Example |
|---------|-----------|---------|
| `{string}` | `string` | `"hello"` |
| `{int}` | `number` | `200` |
| `{float}` | `number` | `0.7` |
| DocString | `string` | Triple-quoted block |
| DataTable | `any` | `dataTable.rows()` |

### Step Reuse

- **Shared steps** go in `common-{layer}.steps.ts` — HTTP verbs, status assertions, common patterns
- **Domain steps** go in `{domain}.steps.ts` — entity-specific setup/teardown
- Never duplicate step patterns — if two files define the same `Given`, playwright-bdd will error

### Path Parameter Resolution

For dynamic paths like `/api/users/{userId}`:

```typescript
function resolvePath(path: string, ctx: MyContext): string {
  return path.replace(/\{(\w+)\}/g, (_, key) => {
    const value = ctx.createdEntities.get(key);
    return value ? String(value) : key;
  });
}
```

## Python Steps (pytest-bdd)

### Imports

```python
from pytest_bdd import scenarios, given, when, then, parsers

# Load feature files (relative to bdd_features_base_dir in pyproject.toml)
scenarios("summarization/summarization-quality.feature")
```

### Context Pattern (State Sharing)

Use a pytest fixture that returns a mutable dict:

```python
@pytest.fixture
def eval_context():
    return {
        "source_article": "",
        "generated_output": "",
        "golden_answer": "",
    }
```

Steps receive it as a parameter:

```python
@given(parsers.parse('the source article "{filename}"'), target_fixture="eval_context")
def load_article(filename, datasets_dir, eval_context):
    eval_context["source_article"] = (datasets_dir / filename).read_text()
    return eval_context

@when(parsers.parse('I generate a summary using prompt "{prompt_id}"'))
def generate(prompt_id, eval_context, prompts_dir):
    # ... use eval_context
```

### Parameter Parsing

Always use `parsers.parse()` for steps with parameters:

```python
@then(parsers.parse("the faithfulness score should be >= {threshold:f}"))
def check_faithfulness(threshold: float, rag_context: dict):
    ...
```

| Format | Type | Example |
|--------|------|---------|
| `{name}` | `str` | Any string |
| `{name:d}` | `int` | `200` |
| `{name:f}` | `float` | `0.7` |

### DocStrings

pytest-bdd passes docstrings via the `docstring` fixture:

```python
@then("the output should pass the rubric:")
def check_rubric(eval_context, docstring):
    rubric_text = docstring.strip()
    ...
```

### Feature File Loading

Feature files are found relative to `bdd_features_base_dir` in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
bdd_features_base_dir = "../../../features/prompt-eval/"
```

So `scenarios("rag/rag-quality.feature")` resolves to `features/prompt-eval/rag/rag-quality.feature`.

## Layer-Specific Patterns

### Acceptance (UI) Steps

```typescript
// Seed data via API (fast), interact via browser (realistic)
Given('a user exists with email {string}', async ({ request }, email) => {
  await request.post('/api/test/seed-user', { data: { email } });
});

// Wait for network before asserting
When('I click the login button', async ({ page }) => {
  const responsePromise = page.waitForResponse('**/api/auth/**');
  await page.getByRole('button', { name: /log in/i }).click();
  await responsePromise;
});

// Use accessible selectors
Then('I should see a welcome message', async ({ page }) => {
  await expect(page.getByText(/welcome/i)).toBeVisible();
});
```

### API Steps

```typescript
// Generic HTTP steps — reuse across all API features
When('I send a POST request to {string} with body:', async ({ request }, path, docString, testInfo) => {
  const ctx = getCtx(testInfo.testId);
  const response = await request.post(resolvePath(path, ctx), { data: JSON.parse(docString) });
  ctx.lastResponse = { status: response.status(), body: await response.json().catch(() => null) };
});

// Generic assertion steps
Then('the response status should be {int}', async ({}, expected, testInfo) => {
  const ctx = getCtx(testInfo.testId);
  expect(ctx.lastResponse.status).toBe(expected);
});
```

### Integration Steps

```typescript
// Service URL from environment
Given('the user service is available at USER_SERVICE_URL', async ({}, testInfo) => {
  const ctx = getCtx(testInfo.testId);
  ctx.serviceUrls.user = process.env.USER_SERVICE_URL || 'http://localhost:3001';
});

// Cross-service request with explicit baseUrl
When('I create an order', async ({ request }, testInfo) => {
  const ctx = getCtx(testInfo.testId);
  const response = await request.post(`${ctx.serviceUrls.order}/api/orders`, { data: { ... } });
});

// Polling for eventual consistency
Then('eventually the inventory should be {int} units', async ({ request }, expected, testInfo) => {
  for (let i = 0; i < 15; i++) {
    const resp = await request.get(`${ctx.serviceUrls.inventory}/api/inventory/${id}`);
    if ((await resp.json()).quantity === expected) return;
    await new Promise(r => setTimeout(r, 1000));
  }
  // Final assertion (fails with clear message)
  expect(finalBody.quantity).toBe(expected);
});
```

### Prompt Eval Steps (TypeScript — promptfoo API)

```typescript
import { assertions } from 'promptfoo';
const { matchesSimilarity, matchesLlmRubric, matchesFactuality } = assertions;

// Semantic similarity
Then('the output should be semantically similar to the golden answer with threshold {float}',
  async ({}, threshold, testInfo) => {
    const ctx = getCtx(testInfo.testId);
    const result = await matchesSimilarity(ctx.generatedOutput, ctx.goldenAnswer, threshold);
    expect(result.pass).toBe(true);
  },
);

// LLM-as-judge rubric
Then('the output should pass the rubric:', async ({}, rubric, testInfo) => {
  const ctx = getCtx(testInfo.testId);
  const result = await matchesLlmRubric(rubric.trim(), ctx.generatedOutput, {});
  expect(result.pass).toBe(true);
});
```

### Prompt Eval Steps (Python — DeepEval)

```python
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

@then(parsers.parse('the output should be factual given "{claim}"'))
def check_factuality(claim, eval_context):
    test_case = LLMTestCase(
        input="Summarize this article",
        actual_output=eval_context["generated_output"],
        retrieval_context=[eval_context["source_article"]],
    )
    assert_test(test_case, [FaithfulnessMetric(threshold=0.7)])
```

### Prompt Eval Steps (Python — Ragas)

```python
from ragas import evaluate
from ragas.metrics import Faithfulness

@then(parsers.parse("the faithfulness score should be >= {threshold:f}"))
def check_faithfulness(threshold, rag_context):
    dataset = EvaluationDataset(samples=[build_sample(rag_context)])
    result = evaluate(dataset=dataset, metrics=[Faithfulness()])
    score = result.scores[0]["faithfulness"]
    assert score >= threshold, f"Faithfulness {score:.2f} < {threshold}"
```

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Put business logic in steps | Put it in `support/helpers/` |
| Hardcode test data in steps | Use factories or datasets |
| Share state via global variables | Use context Map (TS) or fixture dict (Python) |
| Create Page Object classes | Use composable fixtures |
| Duplicate step patterns across files | Put shared steps in `common-*.steps.ts` |
| Mix `page` and `request` in API steps | API steps use `request` only |
| Put assertion thresholds in step code | Put them in the feature file: `>= 0.7` |

## Known Pitfalls (Lessons Learned)

### 1. playwright-bdd does NOT pass `testInfo` to step functions

**Wrong:**
```typescript
Given('something', async ({ request }, name: string, testInfo) => {
  const id = testInfo.testId; // ERROR: testInfo is undefined
});
```

**Right:**
```typescript
Given('something', async ({ request }, name: string) => {
  // Use module-level state. Steps run sequentially within a test,
  // so a simple module-level variable is safe. Reset in Background step.
});
```

playwright-bdd step signatures are `async ({ fixtures }, ...matchedParams)`. There is no `testInfo` parameter. Use module-level state reset in the Background/Given step instead of `testInfo.testId`-keyed Maps.

### 2. Placeholder data must match feature file assertions

When writing placeholder/stub data for dry-run testing, verify it satisfies ALL deterministic assertions in the feature files. If a feature says `the output should contain "carbon emissions"`, the placeholder must include that exact phrase. Run `--grep "@deterministic"` after any placeholder change to catch mismatches immediately.

## Visual Regression Steps

Reusable visual regression steps live in `tests/acceptance/steps/visual-regression.steps.ts`. You don't need to create new steps for new visual tests — just use the existing patterns in feature files:

```gherkin
# Full page screenshot
Then the page should match the visual baseline "login-page"

# Full page with masked dynamic elements
Then the page should match the visual baseline "dashboard" with masked:
  | selector            |
  | .timestamp          |
  | .user-avatar        |

# Single element screenshot
Then the element ".chart" should match the visual baseline "revenue-chart"
```

Steps handle:
- `waitForLoadState('networkidle')` before capturing
- `animations: 'disabled'` to freeze CSS animations
- `fullPage: true` for page-level captures
- Mask array built from data table for dynamic content

Visual diffs are viewable in Playwright HTML report (`npm run report`) — not in the living docs (which show pass/fail only).
