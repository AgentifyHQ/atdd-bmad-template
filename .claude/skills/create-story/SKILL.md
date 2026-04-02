---
name: create-story
description: This skill should be used when the user asks to "create a story", "new story", "add a story", "create story from spec", or provides a BMM story specification to turn into a tracked story. Generates a GitHub Issue, BDD feature file with @story-N tag, and project board entry as an atomic operation.
argument-hint: "[story-spec-path-or-title]"
---

# Create Story

Generate a tracked story as an atomic triple: GitHub Issue + BDD feature file + project board entry. All three are created together — never one without the others.

## Input

Accept story details from:
- `$ARGUMENTS` as a story spec file path or title
- A BMM story spec provided inline (markdown)
- A plain description of what the story covers

## Workflow

### 1. Gather Story Details

Extract or prompt for:
- **Title** — concise name (e.g., "Wire Content Handlers into Interrupt Creation")
- **Source repo** — the application repo this story originates from (e.g., `agent-hitl-gateway`)
- **Layer** — `acceptance`, `api`, `integration`, or `prompt-eval`
- **Domain** — feature domain in kebab-case (e.g., `interrupt-management`, `user-management`)
- **Priority** — `P0`, `P1`, or `P2`

Derive the **epic label** automatically: `{source-repo}::{domain}::{layer-abbreviation}`
- Layer abbreviations: `acceptance` → `acc`, `api` → `api`, `integration` → `int`, `prompt-eval` → `pe`
- Example: `agent-hitl-gateway::interrupt-management::api`

### 2. Ensure Labels Exist

Create GitHub labels if they don't exist in `atdd-bmad-template`:

```bash
gh label create "story" --color "0E8A16" --description "Story tracked via /create-story" -R AgentifyHQ/atdd-bmad-template 2>/dev/null || true
gh label create "P0" --color "B60205" --description "Critical priority" -R AgentifyHQ/atdd-bmad-template 2>/dev/null || true
gh label create "{epic-label}" --color "1D76DB" --description "Epic: {domain} {layer} tests" -R AgentifyHQ/atdd-bmad-template 2>/dev/null || true
```

### 3. Create GitHub Issue

Issues always live in the **atdd-bmad-template** repo (test repo), not the source code repo.

```bash
gh issue create \
  --title "Story: {title}" \
  --body "{story spec markdown}" \
  --label "story,{priority},{epic-label}" \
  -R AgentifyHQ/atdd-bmad-template
```

Capture the issue number from output.

### 4. Create Feature File

**Read convention files first:**
- `.claude/conventions/feature-file-standards.md`
- `.claude/conventions/test-organization.md`

Place the file at: `features/{layer}/{domain}/{kebab-case-title}.feature`

Required tags and structure:

```gherkin
@{layer} @{priority} @github:AgentifyHQ/atdd-bmad-template/issues/{issue-number}
Feature: {title}
  As a {role}
  I want {capability}
  So that {benefit}

  Scenario: {acceptance criterion}
    Given ...
    When ...
    Then ...
```

### 5. Check Step Definitions

Check existing steps before creating new ones:

| Layer | Steps Location |
|-------|---------------|
| UI Acceptance | `tests/acceptance/steps/` |
| API | `tests/api/steps/common-api.steps.ts` |
| Integration | `tests/integration/steps/` |
| Prompt Eval | `tests/prompt-eval/ts-steps/` |

Only create new step files for genuinely new step patterns.

### 6. Add Issue to Sprints Board

Find the repo's Sprints board (titled "{repo-name} Sprints") and add the issue. If it doesn't exist, create one. Read `.claude/conventions/project-management.md` for board discovery queries.

### 7. Handle Epic on Epic Board

Find the org Epic Board (titled "Epic Board"). Read `.claude/conventions/project-management.md` for the full epic lifecycle:
- If a matching draft epic exists in Speccing/Backlog → convert to real issue, move to "In Progress"
- If no epic exists → create a draft
- Add story link to the epic's story table

### 8. Verify

1. Run `npx bddgen` — confirm feature file parses
2. Run `gh issue view {number}` — confirm issue exists
3. Report: issue URL, feature file path, epic status

## Rules

- Read `.claude/conventions/project-management.md` for board operations
- Read `.claude/conventions/feature-file-standards.md` before generating features
- Never create a feature file without a GitHub Issue, or vice versa
- Always include `@github:{owner}/{repo}/issues/{N}` tag
- Epic label format: `{source-repo}::{domain}::{layer-abbrev}`
- Discover board numbers dynamically — never hardcode them
- Issue body IS the story spec — keep it as source of truth
- Reuse existing step definitions; only add new ones for new patterns
