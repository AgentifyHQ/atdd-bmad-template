---
name: probe-test-failures
description: Probe Playwright test failures by cross-referencing the test report with the live app using Chrome browser automation. Use when the user says "probe failures", "debug test failures", "check test results", "why are tests failing", or wants to understand test failures against the running app.
argument-hint: "[report-url] [app-url]"
---

# Probe Test Failures

Systematically investigate Playwright BDD test failures by cross-referencing the test report with the live application using Chrome browser automation. Produces a categorized diagnosis — never guesses, always probes.

## Prerequisites

- Chrome browser automation tools (claude-in-chrome MCP) must be available
- Playwright HTML report must be served (e.g., `npx playwright show-report --port 9323`)
- The application under test must be running locally

## Input

Accept from `$ARGUMENTS` or prompt for:
- **Report URL** — Playwright HTML report URL (default: `http://localhost:9323`)
- **App URLs** — Application URLs to probe against (defaults from `.env`: `SAAS_URL`, `MARKETING_URL`)

If no arguments provided, use defaults:
- Report: `http://localhost:9323`
- SaaS: `http://localhost:3000`
- Marketing: `http://localhost:3001`

## Workflow

Execute these phases sequentially. Do NOT skip phases or jump to conclusions.

### Phase 1: Survey the Report

1. Open the Playwright report URL in a new Chrome tab
2. Click the **"Failed"** filter to show only failures
3. Extract the **full list** of failed test names using `get_page_text`
4. Record: total count, pass count, fail count, skip count
5. Group failures by feature file / test suite

**Output:** A numbered list of all failures grouped by feature file.

### Phase 2: Categorize by Error Type

For each failure group (not each individual test — group by feature file):

1. Click into a **representative failure** from the group
2. Read the **error message** carefully — extract:
   - The locator that failed
   - The expected vs actual values
   - Whether it's a timeout, strict mode violation, element not found, assertion mismatch, etc.
3. Note the **error pattern** — if multiple failures in a group share the same root cause, note that

Common error patterns to watch for:
- **Strict mode violation** → duplicate testids (desktop + mobile layout)
- **Element not found / timeout** → wrong selector, element doesn't exist, or page didn't load
- **Assertion mismatch** → wrong expected value (stale test data)
- **Navigation timeout** → app not running or wrong URL

**Output:** Error pattern for each failure group.

### Phase 3: Probe the Live App

For each unique error pattern, verify against the actual application:

1. Open the relevant app URL in a new Chrome tab
2. Navigate to the page the test targets
3. Use `javascript_tool` to inspect the DOM:
   - Check if expected `data-testid` attributes exist
   - Check actual text content vs what tests expect
   - Check element counts (are there duplicates from responsive layouts?)
   - Check ARIA roles (`role="tab"` vs `role="button"`, etc.)
   - Check scroll anchors, href attributes, CSS classes
4. Take screenshots of the actual app state for reference

Key JS probes to run:
```javascript
// Check all data-testid elements
[...document.querySelectorAll('[data-testid]')].map(el => ({
  testid: el.getAttribute('data-testid'),
  tag: el.tagName,
  visible: el.offsetParent !== null
}));

// Check specific element text
document.querySelector('[data-testid="X"]')?.textContent?.trim();

// Check element count (detect duplicates)
document.querySelectorAll('[data-testid="X"]').length;

// Check ARIA roles
[...document.querySelectorAll('[role]')].map(el => ({
  role: el.getAttribute('role'),
  text: el.textContent.trim().substring(0, 50)
}));
```

**Output:** For each error pattern, what the app actually shows vs what the test expects.

### Phase 4: Diagnose Root Causes

Cross-reference Phase 2 (error messages) with Phase 3 (actual app state) to classify each failure into exactly one category:

| Category | Meaning | Fix Location |
|----------|---------|-------------|
| **Test Bug — Wrong Assertion** | Test expects wrong value (stale data, wrong selector, wrong count) | Feature file or step definition |
| **Test Bug — Infrastructure** | Shared test helper has a bug (e.g., missing `.first()`, wrong locator strategy) | Step definition or support helper |
| **App Bug** | The app is genuinely broken — element missing, wrong text, broken interaction | Application code |
| **Environment Issue** | App not running, wrong port, auth redirect, missing test data | Environment / config |
| **Flake** | Timing-dependent — passes sometimes, fails sometimes | Step definition (add waits/retries) |

**CRITICAL:** Do not label anything as "App Bug" unless you confirmed the element/behavior is genuinely wrong by inspecting the live app. If the test expects something that never existed (stale source data), that's a Test Bug, not an App Bug.

### Phase 5: Present Findings

Present a findings table with this exact format:

```
## Test Failure Probe — Findings

**Report:** {url} | **Run:** {date} | **Total:** {n} | **Pass:** {n} | **Fail:** {n}

### Summary by Category

| Category | Count | Fix Location |
|----------|:---:|-------------|
| Test Bug — Wrong Assertion | N | Feature files |
| Test Bug — Infrastructure | N | Step definitions |
| App Bug | N | App code |
| Environment Issue | N | Config |
| Flake | N | Step definitions |

### Detailed Findings

| # | Test Name | Category | Root Cause | Recommended Fix |
|---|-----------|----------|-----------|----------------|
| 1 | ... | ... | ... | ... |
```

After presenting findings, ask:

> Want me to fix the test bugs now? (I will not touch app code — app bugs should be filed as issues.)

## Rules

- **Never guess.** Every diagnosis must be backed by evidence from the report AND the live app.
- **Never touch app code.** This skill only fixes test code. App bugs produce issue recommendations.
- **Probe before diagnosing.** Don't read an error message and assume — always verify against the live app.
- **Group before drilling.** Survey all failures first, then investigate by group — don't click into every single test individually.
- **Preserve the Murat persona** if it's active — findings should be framed in risk/impact language.
