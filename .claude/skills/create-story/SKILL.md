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

### 6. Add Issue to Story Board

Add issue to the **repo story board** (project #5 — "atdd-bmad-template Stories"):

```bash
gh project item-add 5 --owner AgentifyHQ \
  --url https://github.com/AgentifyHQ/atdd-bmad-template/issues/{issue-number}
```

If the story board doesn't exist, create one:

```bash
gh api graphql -f query='mutation { createProjectV2(input: {
  ownerId: "{org-node-id}" title: "atdd-bmad-template Stories"
  repositoryId: "{repo-node-id}"
}) { projectV2 { id number url } } }'
```

### 7. Ensure Epic Exists on Epic Board

The **org Epic Board** (project #4) tracks epics, not stories. Check if an epic entry for this domain exists; if not, add a draft issue:

```bash
# Add epic as draft issue on Epic Board (project #4)
gh api graphql -f query='mutation { addProjectV2DraftIssue(input: {
  projectId: "PVT_kwDOEBTe684BTfAQ"
  title: "{source-repo}::{domain}::{layer-abbrev}"
  body: "Epic: {description}\n\nFeature files:\n- features/{layer}/{domain}/{file}.feature"
}) { projectItem { id } } }'
```

Skip this step if the epic already exists on the board.

### 8. Verify

1. Run `npx bddgen` — confirm feature file parses
2. Run `gh issue view {number} -R AgentifyHQ/atdd-bmad-template` — confirm issue
3. Report: issue URL, feature file path, epic label, story board status

## Rules

- Issues live in **atdd-bmad-template** (test repo), never in source code repos
- **Two boards:** org Epic Board (#4) for epics, repo Story Board (#5) for stories
- Epic label format: `{source-repo}::{domain}::{layer-abbrev}`
- Auto-create story board if none exists
- Read convention files before generating any feature file
- Always include `@github:AgentifyHQ/atdd-bmad-template/issues/{N}` tag — this links tests to issues
- Never create a feature file without a GitHub Issue, or vice versa
- Issue body IS the story spec — keep it as source of truth
- Reuse existing step definitions; only add new ones for new patterns
