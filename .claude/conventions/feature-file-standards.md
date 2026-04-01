# Convention: Feature File Standards

## Template

Every feature file follows this structure:

```gherkin
@{layer} @P{priority}
Feature: {Domain} {Behavior}
  As a {role/persona}
  I want to {action}
  So that {business value}

  Background:
    Given {common precondition shared by all scenarios}

  @{category} @smoke
  Scenario: {Happy path — concise, active voice}
    Given {specific precondition}
    When {user/system action}
    Then {observable outcome}
    And {additional assertion}

  @negative
  Scenario: {Error condition — what goes wrong}
    When {invalid action}
    Then {error response or message}

  Scenario Outline: {Parameterized — describe the pattern}
    When {action with "<param>"}
    Then {outcome with "<expected>"}

    Examples:
      | param  | expected |
      | value1 | result1  |
      | value2 | result2  |
```

## Required Tags

Every feature file MUST have these tags on the `Feature` line:

| Tag | Required | Values | Purpose |
|-----|----------|--------|---------|
| Layer | Yes | `@acceptance`, `@api`, `@integration`, `@prompt-eval` | Identifies which project runs it |
| Priority | Yes | `@P0` (critical), `@P1` (high), `@P2` (medium) | Filters for release gates |

## Optional Tags (on Scenario level)

| Tag | When to Use |
|-----|-------------|
| `@smoke` | Quick sanity check subset — one happy path per feature |
| `@negative` | Error cases, invalid input, boundary conditions |
| `@eventual-consistency` | Integration tests using polling assertions |
| `@deterministic` | Prompt eval: free, fast checks (word count, contains) |
| `@semantic` | Prompt eval: embedding similarity checks |
| `@llm-judge` | Prompt eval: LLM-as-judge rubric checks |
| `@faithfulness` | Prompt eval: grounding/hallucination checks |
| `@rag` | Prompt eval: RAG pipeline metrics |
| `@safety` | Prompt eval: banned patterns, guardrails |
| `@wip` | Work in progress — excluded from CI |

## Writing Rules

### Scenarios
- **Active voice, present tense**: "User creates an order", not "An order was created by the user"
- **One behavior per scenario**: Don't test login + checkout in the same scenario
- **Happy path first, then edge cases**: Smoke scenario should be the first in the file
- **Scenario names are unique within a feature**: No duplicates

### Given/When/Then
- **Given**: Setup state — data exists, user is logged in, service is available
- **When**: Single action — click, send request, generate output
- **Then**: Observable outcome — status code, visible text, score threshold
- **And**: Continuation of the previous step type — not a new action after a Then

### DocStrings (multi-line data)
Use triple-quoted docstrings for JSON bodies and rubrics:

```gherkin
When I send a POST request to "/api/users" with body:
  """json
  {
    "name": "James",
    "email": "james@test.com"
  }
  """

Then the output should pass the rubric:
  """
  The summary must be neutral and professional.
  """
```

### Data Tables
Use tables for parameterized assertions or lists:

```gherkin
Then the output should contain any of:
  | term           |
  | greenhouse     |
  | climate change |
```

### Scenario Outlines
Use for testing the same behavior with multiple inputs:

```gherkin
Scenario Outline: Output must not contain banned patterns
  When I generate a summary using prompt "summarize-v1"
  Then the output should not contain "<banned>"

  Examples:
    | banned     |
    | SSN        |
    | credit card|
    | <script>   |
```

## Layer-Specific Conventions

### Acceptance (UI)
- Seed data via API in `Given` steps (fast), interact via browser in `When` steps
- Use `data-testid` or ARIA roles for selectors — never CSS classes
- Intercept network responses before navigation (network-first pattern)

### API
- Use generic HTTP step patterns: `I send a {METHOD} request to "{path}"`
- Path parameters use `{entityId}` syntax, resolved from context
- Always assert status code + body content, not just one

### Integration
- Always declare service URLs in Background: `Given the {name} service is available at {ENV_VAR}`
- Use polling for eventual consistency: `eventually the {thing} should be {value}`
- Set reasonable poll limits (15 attempts, 1s interval)

### Visual Regression (Acceptance)
- Tag with `@visual` — visual tests are optional, heavier than functional tests
- Use `the page should match the visual baseline "{name}"` for full-page screenshots
- Use `with masked:` data table to exclude dynamic content (timestamps, avatars, counts)
- Baselines stored in `tests/{testDir}/__snapshots__/` — committed to git
- Update baselines: `npx playwright test --update-snapshots --grep @visual`
- **Review visual diffs in Playwright HTML report** (`npm run report`) — it has an interactive slider. Living docs show pass/fail only.
- Run in Docker/CI for cross-platform consistency — font rendering differs across OS

### Prompt Eval
- Tag by evaluation layer: `@deterministic`, `@semantic`, `@llm-judge`, `@faithfulness`, `@rag`
- Reference prompts by ID: `I generate a summary using prompt "summarize-v1"`
- Reference datasets by filename: `the source article "article-climate.txt"`
- Rubrics go in docstrings, not hardcoded in steps
- Threshold values go in the Then step: `with threshold 0.7`, `>= 0.7`

## Design Assets

Place Figma exports, mockups, or reference screenshots in an `assets/` folder alongside feature files:

```
features/acceptance/user-management/
├── user-login.feature
├── user-login-visual.feature
└── assets/
    ├── login-page.png
    └── dashboard.png
```

- The build script auto-detects `assets/` and embeds a scrollable gallery on the living docs page
- Use descriptive filenames: `login-page.png` → label "Login Page"
- All features in the same domain share the same `assets/` directory
- Supported: PNG, JPG, SVG, WebP, GIF
- Images are cache-busted with content hash — no stale browser cache issues
- Click any thumbnail in the living docs to view full-size (lightbox)

## File Organization

```
features/{layer}/{domain}/{descriptive-name}.feature
```

- **Domain** groups related behaviors: `user-management`, `orders`, `billing`, `summarization`, `rag`
- **One feature per file** — don't combine unrelated behaviors
- **Feature name matches filename**: `user-crud.feature` contains `Feature: User CRUD API`

## Known Pitfalls (Lessons Learned)

### 1. Step text must EXACTLY match the step definition pattern — including grammar

`bddgen` matches feature file step text against step definition patterns character-by-character. A singular/plural mismatch causes "Missing step definition" errors.

**Broken:**
```gherkin
# Feature says "1 unit" (singular)
When I create an order for user with 1 unit of "WIDGET-002"
```
```typescript
// Step expects "units" (plural) — DOES NOT MATCH
When('I create an order for user with {int} units of {string}', ...)
```

**Fix:** Either change the feature to match the step (`1 units`) or write the step pattern to handle both forms. The safest approach: keep Gherkin phrasing consistent across all scenarios in a feature and match the step definition exactly.

### 2. All feature files under a glob must have matching TS steps

`defineBddConfig({ features: 'features/prompt-eval/**/*.feature' })` picks up ALL `.feature` files under that path. If you add a feature file with steps intended only for Python (pytest-bdd), playwright-bdd will still try to match those steps and fail with "Missing step definitions."

**Solution:** Every step pattern used in `features/prompt-eval/` must have a corresponding step definition in `tests/prompt-eval/ts-steps/`. For RAG-specific scenarios, the TS steps can use promptfoo's `matchesFactuality`/`matchesLlmRubric` as proxies for the full Ragas metrics. The Python runner provides the deep evaluation; the TS runner provides a lighter-weight check against the same spec.

### 3. Never use `loading="lazy"` on images in living docs

MkDocs Material's `navigation.instant` feature loads pages via XHR without a full browser navigation. This means the browser's lazy loading observer is never triggered for images that are already "in the viewport." Images will appear broken.

**Solution:** The build script renders `<img>` tags without `loading="lazy"`. If you add images manually to any generated markdown, do not add lazy loading.
