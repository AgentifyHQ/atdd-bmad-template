# Convention: Prompt Evaluation

## Core Principle

Prompt evaluation uses the same BDD approach as every other layer. Feature files define **what** quality means. Step definitions define **how** to measure it.

```
Feature file (stakeholder-readable)     Step definition (engineering)
────────────────────────────────────    ─────────────────────────────
"the output should be faithful"    →    DeepEval FaithfulnessMetric
"the output should pass rubric"    →    promptfoo matchesLlmRubric()
"the faithfulness score >= 0.7"    →    Ragas Faithfulness metric
"the output should be under 200"   →    word count assertion
```

## Layered Evaluation Strategy

Evaluations are organized by cost and speed. Tag scenarios by layer:

| Layer | Tag | Cost | Tool | Runner |
|-------|-----|------|------|--------|
| 1. Deterministic | `@deterministic` | Free | Native assertions | Both |
| 2. Semantic | `@semantic` | ~$0.001/eval | promptfoo embeddings | TS (playwright-bdd) |
| 3. LLM-as-Judge | `@llm-judge` | ~$0.01-0.05/eval | promptfoo + DeepEval GEval | Both |
| 4. RAG Metrics | `@rag` | ~$0.01-0.05/eval | Ragas | Python (pytest-bdd) |
| 5. Red-teaming | standalone | ~$0.05+/eval | promptfoo CLI | Not BDD |

## Dual-Runner Architecture

Two BDD runners share the same feature files in `features/prompt-eval/`:

### TypeScript Runner (playwright-bdd + promptfoo API)
- Steps: `tests/prompt-eval/ts-steps/prompt-eval.steps.ts`
- Covers: Deterministic, semantic similarity, LLM-as-judge, factuality
- API: `promptfoo.assertions.matchesSimilarity()`, `matchesLlmRubric()`, `matchesFactuality()`
- Run: `npm run test:prompt-eval`

### Python Runner (pytest-bdd + DeepEval + Ragas)
- Steps: `tests/prompt-eval/python/test_deepeval_*.py`, `test_ragas_*.py`
- Covers: Faithfulness, hallucination, RAG metrics, custom rubrics
- API: `deepeval.assert_test()`, `ragas.evaluate()`
- Run: `npm run test:prompt-eval:python`

### Overlap is OK — but TS steps are MANDATORY for all feature files

Some steps (deterministic checks) exist in both runners. This is intentional redundancy — either runner can catch regressions independently.

**Critical:** `defineBddConfig` globs ALL `.feature` files under `features/prompt-eval/`. This means every step pattern — including RAG-specific ones like `the faithfulness score should be >= {float}` — MUST have a corresponding TypeScript step definition. If you add a feature file with Python-only intent, playwright-bdd will fail with "Missing step definitions" during `bddgen`.

For Python-specialized metrics (Ragas context precision, recall), the TS steps use promptfoo's `matchesFactuality`/`matchesLlmRubric`/`matchesSimilarity` as lighter-weight proxies. The Python runner provides the full evaluation; the TS runner provides a complementary check.

## Standalone Tools (Not BDD)

These are exploratory, not quality gates:

| Tool | Command | Purpose |
|------|---------|---------|
| Prompt comparison | `npm run prompt:compare` | Side-by-side prompt/model matrix |
| Comparison viewer | `npm run prompt:compare:view` | Interactive browser UI |
| Red-teaming | `npm run prompt:redteam` | Security vulnerability scan |

Config: `tests/prompt-eval/promptfoo/promptfooconfig.yaml`

## Adding a New Prompt Evaluation

### Step 1: Create the feature file

Place in the appropriate subdirectory:

```
features/prompt-eval/
├── summarization/    # Output quality (length, tone, accuracy)
├── rag/              # RAG pipeline (faithfulness, context quality)
├── safety/           # Guardrails (banned content, prompt injection)
├── classification/   # Classification accuracy (add new domains here)
└── agent/            # Agent behavior (tool selection, planning)
```

Follow the template:

```gherkin
@prompt-eval @P0
Feature: {Domain} {Quality Aspect}
  As a {role}
  I want {quality criteria}
  So that {business value}

  Background:
    Given the source article "{dataset-filename}.txt"

  @deterministic @smoke
  Scenario: {Fast, free check}
    When I generate a summary using prompt "{prompt-id}"
    Then the output should be under {N} words

  @llm-judge
  Scenario: {Quality rubric check}
    When I generate a summary using prompt "{prompt-id}"
    Then the output should pass the rubric:
      """
      {rubric criteria here}
      """
```

### Step 2: Add datasets (if needed)

Place in `tests/prompt-eval/promptfoo/datasets/`:
- Article: `article-{topic}.txt`
- Golden answer: `golden-summary-{topic}.txt`

Both TS and Python steps read from this directory.

### Step 3: Add prompts (if needed)

Place in `tests/prompt-eval/promptfoo/prompts/`:
- Format: `{purpose}-v{version}.txt`
- Use `{{variable}}` for template parameters

### Step 4: Add step definitions (if new step patterns needed)

- If using existing step patterns (e.g., "the output should contain"), no new steps needed.
- For new assertion types:
  - **TS**: Add to `tests/prompt-eval/ts-steps/prompt-eval.steps.ts`
  - **Python**: Add to appropriate `test_*.py` in `tests/prompt-eval/python/`

### Step 5: Wire up scenarios (Python only)

In the Python test file, add the `scenarios()` call:

```python
scenarios("classification/intent-detection.feature")
```

The TS side picks up features automatically via the glob in `playwright.config.ts`.

## Thresholds

Put thresholds in the feature file, not in step code:

```gherkin
# Good — threshold in the spec
Then the faithfulness score should be >= 0.7

# Bad — threshold hidden in code
Then the output should be faithful
```

This makes quality gates visible to stakeholders and auditable in the living docs.

## Recommended Thresholds

| Metric | Minimum | Target | Notes |
|--------|---------|--------|-------|
| Faithfulness | 0.7 | 0.85 | Lower = hallucination risk |
| Answer Relevancy | 0.7 | 0.85 | Lower = off-topic responses |
| Context Precision | 0.6 | 0.8 | Lower = noisy retrieval |
| Context Recall | 0.7 | 0.85 | Lower = missing information |
| Factual Correctness | 0.7 | 0.9 | Lower = wrong facts |
| Semantic Similarity | 0.65 | 0.8 | Lower = answer drift |

Start at minimums, raise to targets as the system matures.

## Environment & API Keys

All runners load from a single `.env` file in the project root:

| Runner | How `.env` is loaded |
|--------|---------------------|
| playwright-bdd (TS) | `import 'dotenv/config'` in `playwright.config.ts` |
| pytest-bdd (Python) | `load_dotenv()` in `conftest.py` |
| promptfoo CLI | Auto-loads `.env` |

Keys needed by tag:

| Tag | Keys Required |
|-----|--------------|
| `@deterministic` | None |
| `@semantic` | `OPENAI_API_KEY` (for embeddings) |
| `@llm-judge` | `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` |
| `@faithfulness`, `@rag` | `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` |

## Connecting to Your LLM

Both runners have placeholder generation functions. Replace them before running against real services:

- **TS**: `tests/prompt-eval/ts-steps/prompt-eval.steps.ts` — the `When` step that calls `request.post()`
- **Python**: `tests/prompt-eval/python/conftest.py` — `generate_llm_output()` and `generate_rag_answer()`

## CI Trigger

Prompt eval runs when PRs have the `prompt-change` label. See `docs/ci-integration.md` for the full pipeline config.

## Known Pitfalls (Lessons Learned)

### 1. Every feature file needs TS steps — even Python-intended ones

The playwright-bdd glob (`features/prompt-eval/**/*.feature`) picks up ALL feature files. If you create a RAG feature file with steps like `the faithfulness score should be >= 0.7` and only implement it in Python, `bddgen` will fail. Always add a TS step implementation (using promptfoo's API as a proxy) for every step pattern.

### 2. Placeholder output must satisfy ALL deterministic assertions

When updating placeholder/stub LLM output in step definitions, cross-check it against every `@deterministic` scenario's assertions. Run `npx playwright test --project=prompt-eval --grep "@deterministic"` immediately after any placeholder change to catch mismatches before they cascade.

### 3. `matchesLlmRubric`, `matchesFactuality`, `matchesSimilarity` require API keys

These promptfoo assertion functions call external LLM APIs. Without `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` set, they throw connection errors. Tests tagged `@semantic`, `@llm-judge`, `@rag`, and `@faithfulness` will fail without keys. Only `@deterministic` tests run without any API key.
