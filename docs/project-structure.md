# Project Structure

```
features/                              # Gherkin feature files (the WHAT)
├── acceptance/                        # UI acceptance scenarios
│   └── {domain}/
│       ├── *.feature                  #   Feature specs
│       └── assets/                    #   Design mockups (Figma exports, screenshots)
├── api/                               # API contract scenarios
├── integration/                       # Cross-service scenarios
└── prompt-eval/                       # Prompt quality specifications
    ├── summarization/                 #   Output quality criteria
    ├── rag/                           #   RAG pipeline quality criteria
    └── safety/                        #   Safety guardrail criteria

tests/                                 # Step definitions (the HOW)
├── acceptance/steps/                  # UI steps (page + request)
│   ├── *-login.steps.ts              #   Functional steps
│   └── visual-regression.steps.ts    #   Visual baseline steps (@visual)
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
