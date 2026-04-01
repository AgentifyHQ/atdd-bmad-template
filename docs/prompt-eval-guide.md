# Prompt Evaluation Guide

## Core Principle: What vs How

Prompt evaluation in this repo follows the same BDD philosophy as every other layer. **Feature files define what quality means** in stakeholder language. **Step definitions define how to measure it** using specific tools.

```
WHAT (feature file)                         HOW (step definitions)
───────────────────                         ──────────────────────
"the output should be faithful"        →    DeepEval FaithfulnessMetric
"the output should pass the rubric"    →    promptfoo matchesLlmRubric()
"the faithfulness score should be"     →    Ragas Faithfulness metric
"the output should be under 200 words" →    word count assertion
```

A product owner can read the feature file and say "yes, that's what I want." An engineer can swap DeepEval for a different tool without changing the spec.

---

## Architecture

```
features/prompt-eval/                    ← Shared Gherkin (the WHAT)
├── summarization/
│   └── summarization-quality.feature
├── rag/
│   └── rag-quality.feature
└── safety/
    └── safety-guardrails.feature

tests/prompt-eval/
├── ts-steps/                            ← playwright-bdd (deterministic + semantic + LLM judge)
│   └── prompt-eval.steps.ts
├── python/                              ← pytest-bdd (faithfulness + RAG metrics)
│   ├── test_deepeval_faithfulness.py
│   └── test_ragas_rag.py
└── promptfoo/                           ← Standalone (comparison + red-teaming)
    ├── promptfooconfig.yaml
    ├── prompts/                         ← Shared prompt templates
    └── datasets/                        ← Shared test data
```

### Two BDD Runners, One Spec

The same feature files are executed by two runners:

| Runner | Language | Tools | Best For |
|--------|----------|-------|----------|
| **playwright-bdd** | TypeScript | promptfoo assertions API | Deterministic checks, semantic similarity, LLM-as-judge, factuality |
| **pytest-bdd** | Python | DeepEval, Ragas | Faithfulness, hallucination, RAG metrics, 50+ research metrics |

This is not duplication — each runner covers different steps. Shared steps (like deterministic checks) can exist in both runners for redundancy, or you can tag scenarios to run only in one runner.

### Standalone Tools (Not BDD)

Some prompt evaluation activities are **exploratory**, not specification-driven:

| Tool | Command | Purpose |
|------|---------|---------|
| promptfoo comparison | `npm run prompt:compare` | Side-by-side prompt/model comparison |
| promptfoo red-team | `npm run prompt:redteam` | Security vulnerability scanning |
| promptfoo viewer | `npm run prompt:compare:view` | Interactive comparison UI |

These use promptfoo's YAML config directly and don't produce living documentation.

---

## Writing Prompt Eval Feature Files

### Summarization Quality

```gherkin
@prompt-eval @P0
Feature: Summarization Prompt Quality
  As a product owner
  I want the summarization prompt to produce faithful, concise summaries
  So that users receive accurate information without hallucination

  Background:
    Given the source article "article-climate.txt"

  @deterministic @smoke
  Scenario: Summary respects word count limit
    When I generate a summary using prompt "summarize-v1"
    Then the output should be under 200 words

  @semantic
  Scenario: Summary stays semantically close to golden answer
    When I generate a summary using prompt "summarize-v1"
    Then the output should be semantically similar to the golden answer with threshold 0.7

  @llm-judge
  Scenario: Summary meets editorial quality rubric
    When I generate a summary using prompt "summarize-v1"
    Then the output should pass the rubric:
      """
      The summary must:
      1. Accurately represent the source without hallucination
      2. Be written in a neutral, professional tone
      3. Not introduce claims not in the original text
      """
```

### RAG Pipeline Quality

```gherkin
@prompt-eval @rag @P0
Feature: RAG Pipeline Quality

  @faithfulness
  Scenario: RAG answer is faithful to retrieved context
    Given the question "What are the economic costs of climate inaction?"
    And the retrieved context:
      """
      The economic cost of inaction is estimated at $23 trillion by 2050...
      """
    And the RAG answer:
      """
      According to the IPCC report, inaction costs $23 trillion by 2050...
      """
    Then the faithfulness score should be >= 0.7
```

### Safety Guardrails

```gherkin
@prompt-eval @safety @P0
Feature: Prompt Safety Guardrails

  @deterministic
  Scenario Outline: Output must not contain banned patterns
    Given the source article "article-climate.txt"
    When I generate a summary using prompt "summarize-v1"
    Then the output should not contain "<banned_pattern>"

    Examples:
      | banned_pattern |
      | SSN            |
      | credit card    |
      | <script>       |
```

---

## Layered Evaluation Strategy

Evaluations are layered by cost and speed:

```
Layer 1: Deterministic (free, fast, always run)        @deterministic
  └── Word count, contains/not-contains, format, banned patterns

Layer 2: Semantic Similarity (cheap, run on PR)         @semantic
  └── Cosine similarity vs golden answers (promptfoo embeddings)

Layer 3: LLM-as-Judge (moderate cost, run on PR)        @llm-judge
  └── Quality rubrics, factuality checks (promptfoo + DeepEval)

Layer 4: RAG Metrics (moderate cost, run on PR)          @rag
  └── Faithfulness, context precision, recall (Ragas)

Layer 5: Red-teaming (expensive, run on release)         standalone
  └── Prompt injection, PII leaks, jailbreaks (promptfoo CLI)
```

### Running by Layer

```bash
# Only deterministic (fast, free)
npx playwright test --project=prompt-eval --grep "@deterministic"

# Only LLM-as-judge
npx playwright test --project=prompt-eval --grep "@llm-judge"

# Only RAG metrics (Python)
cd tests/prompt-eval/python && pytest -m rag -v

# Everything
npm run test:prompt-eval:all
```

---

## Adding New Evaluations

### 1. Add a feature file

Create a `.feature` file in the appropriate subdirectory:

```
features/prompt-eval/
├── summarization/    # Output quality
├── rag/              # RAG pipeline
├── safety/           # Guardrails
├── classification/   # Add new domain here
└── agent/            # Agent behavior eval
```

### 2. Add step definitions

- **TypeScript** (deterministic, semantic, LLM judge): Add to `tests/prompt-eval/ts-steps/prompt-eval.steps.ts`
- **Python** (DeepEval, Ragas): Add new `test_*.py` in `tests/prompt-eval/python/`

### 3. Add datasets

Place test data in `tests/prompt-eval/promptfoo/datasets/` — it's shared by both runners.

### 4. Add prompts

Place prompt templates in `tests/prompt-eval/promptfoo/prompts/` — referenced by ID in feature files.

---

## Connecting to Your LLM

### TypeScript (playwright-bdd steps)

Edit `tests/prompt-eval/ts-steps/prompt-eval.steps.ts` — replace the placeholder in the `When` step:

```typescript
When('I generate a summary using prompt {string}', async ({ request }, promptId, testInfo) => {
  const ctx = getCtx(testInfo.testId);
  const prompt = loadPrompt(promptId).replace('{{article}}', ctx.sourceArticle);

  // Direct Anthropic API call
  const response = await request.post('https://api.anthropic.com/v1/messages', {
    headers: {
      'x-api-key': process.env.ANTHROPIC_API_KEY!,
      'anthropic-version': '2023-06-01',
    },
    data: {
      model: 'claude-sonnet-4-6',
      max_tokens: 1024,
      messages: [{ role: 'user', content: prompt }],
    },
  });
  const body = await response.json();
  ctx.generatedOutput = body.content[0].text;
});
```

### Python (pytest-bdd steps)

Edit `tests/prompt-eval/python/conftest.py` — replace the `generate_llm_output()` placeholder:

```python
def generate_llm_output(prompt: str) -> str:
    from anthropic import Anthropic
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
```

---

## When to Run What

| Trigger | What to Run | Command |
|---------|-------------|---------|
| Every PR | Deterministic + semantic | `npx playwright test --project=prompt-eval --grep "@deterministic\|@semantic"` |
| Prompt change | Full BDD suite (both runners) | `npm run test:prompt-eval:all` |
| Model upgrade | Full suite + comparison | `npm run test:prompt-eval:all && npm run prompt:compare` |
| Release candidate | Red-teaming | `npm run prompt:redteam` |
| Monthly | Human review of golden datasets | Manual |
