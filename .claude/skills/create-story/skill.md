---
name: create-story
description: Create a new story from a BMM spec — generates GitHub Issue, BDD feature file with @story-N tag, and adds to project board. Use when user says "create story", "add story", "new story from spec", or provides a BMM story specification.
user_invocable: true
---

# Create Story

Create a complete story from a BMM story specification. This is an atomic operation that produces:

1. A GitHub Issue in the current repo
2. A BDD feature file tagged with `@story-{issue-number}`
3. The issue added to the org project board in "Speccing" column

## Input

The user provides either:
- A BMM story spec (markdown)
- A reference to a story spec file
- A description of what the story should cover

## Process

### Step 1: Determine story details

From the spec, extract or ask for:
- **Title**: concise story name (e.g., "User Login")
- **Layer**: acceptance, api, integration, or prompt-eval
- **Domain**: the feature domain (e.g., user-management, orders)
- **Epic label**: which epic this belongs to (e.g., epic-1, epic-2)
- **Priority**: P0, P1, or P2

### Step 2: Create the GitHub Issue

```bash
gh issue create \
  --title "Story: {title}" \
  --body "{BMM story spec markdown}" \
  --label "story,{epic-label},{priority}" \
  -R {current-repo}
```

Capture the issue number from the output.

### Step 3: Create the feature file

Read the relevant convention files FIRST:
- `.claude/conventions/feature-file-standards.md`
- `.claude/conventions/test-organization.md`

Generate the feature file at:
```
features/{layer}/{domain}/{kebab-case-title}.feature
```

The feature file MUST include:
- `@{layer}` tag
- `@{priority}` tag (P0, P1, P2)
- `@story-{issue-number}` tag
- Feature description from the BMM spec (As a / I want / So that)
- Scenarios derived from acceptance criteria
- Background section if applicable

Example:
```gherkin
@api @P0 @story-42
Feature: User CRUD API
  As a service consumer
  I want to manage users via the REST API
  So that user data is consistently maintained

  Scenario: Create a new user
    When I send a POST request to "/api/users" with body:
      ...
```

### Step 4: Create step definitions (if new patterns needed)

Check if existing step definitions cover the scenarios:
- `tests/acceptance/steps/` for UI steps
- `tests/api/steps/common-api.steps.ts` for API steps
- `tests/integration/steps/` for integration steps
- `tests/prompt-eval/ts-steps/` for prompt eval steps

Only create new step files if the scenarios use step patterns that don't exist yet.

### Step 5: Add issue to project board

```bash
# Add to org project board
gh project item-add 3 --owner AgentifyHQ --url https://github.com/{repo}/issues/{issue-number}

# Move to "Speccing" column
# (use the GraphQL mutation from scripts/update-story-status.py pattern)
```

### Step 6: Verify

1. Run `npx bddgen` to verify feature file parses correctly
2. Confirm issue exists: `gh issue view {number}`
3. Report back with:
   - Issue URL
   - Feature file path
   - Board status

## Important Rules

- ALWAYS read convention files before generating feature files
- ALWAYS include `@story-{N}` tag — this is the link between tests and issues
- NEVER create a feature file without a corresponding GitHub Issue
- NEVER create an issue without a corresponding feature file
- Feature file and issue are created as a pair — atomic operation
- Use existing step definitions when possible — only create new ones for genuinely new step patterns
- The issue body IS the BMM story spec — keep it as the source of truth
