# Convention: Project Management

## Two-Board System

| Board | Scope | Columns | Items | Naming |
|-------|-------|---------|-------|--------|
| **Epic Board** | Org-level (AgentifyHQ) | Backlog → Speccing → In Progress → Done | Epic issues or drafts | "Epic Board" |
| **Sprints Board** | Per-repo | Todo → In Progress → Done | Story issues | "{repo-name} Sprints" |

The Epic Board is shared across all repos. Each repo that uses this template gets its own Sprints board.

## Epic Lifecycle

### 1. Backlog / Speccing (Manual)

Epics start as **draft issues** on the Epic Board. Created manually or by BMAD workflows (bmad-create-epics-and-stories, bmad-sprint-planning, etc.). No source repo needed yet.

**Epic title format:** `{source-repo}::{domain}::{layer-abbrev}`
- Layer abbreviations: `acceptance` → `acc`, `api` → `api`, `integration` → `int`, `prompt-eval` → `pe`
- Example: `agent-hitl-gateway::interrupt-management::api`

### 2. In Progress (Triggered by /create-story)

When `/create-story` is called and a matching draft epic exists on the board:

1. **Convert** draft → real issue in the source repo (repo exists because a story spec exists)
2. **Move** epic to "In Progress" column
3. **Populate** epic body with BMM epic spec + story links table
4. **Create** story issue in this test repo
5. **Link** story in the epic's story table

If no draft exists, `/create-story` creates a new epic issue directly.

### 3. Done (Automated by CI)

After test runs, CI:
- Updates the story status table in the epic issue body
- Moves epic to "Done" when all linked stories pass
- Moves back to "In Progress" if any story fails

## Story Workflow

### Creating Stories

Use `/create-story` to create a story. It produces an atomic triple:

1. **GitHub Issue** in this test repo (body = story spec, labels: `story`, priority, epic)
2. **Feature file** at `features/{layer}/{domain}/{name}.feature` tagged `@github:{owner}/{repo}/issues/{N}`
3. **Sprints board entry** + link in parent epic's story table

### CI Automation

After tests run, `scripts/update-story-status.py`:
- Parses `@github:` tags from cucumber JSON results
- Labels story issues `tests-passing` or `tests-failing`
- Updates story table in parent epic issue
- Moves epic board column based on aggregate story status

## Finding Boards

Do not hardcode board numbers. Discover them dynamically:

```bash
# Find Epic Board (org-level, titled "Epic Board")
gh api graphql -f query='{ organization(login: "AgentifyHQ") {
  projectsV2(first: 20) { nodes { number title } }
} }' --jq '.data.organization.projectsV2.nodes[] | select(.title == "Epic Board") | .number'

# Find Sprints Board (look for "{repo-name} Sprints")
gh api graphql -f query='{ organization(login: "AgentifyHQ") {
  projectsV2(first: 20) { nodes { number title } }
} }' --jq '.data.organization.projectsV2.nodes[] | select(.title | endswith("Sprints")) | .number'
```

## Labels

| Label | Color | Purpose |
|-------|-------|---------|
| `story` | green | Story issue tracked via `/create-story` |
| `P0` / `P1` / `P2` | red / orange / yellow | Priority |
| `{repo}::{domain}::{layer}` | blue | Links story to its parent epic |
| `tests-passing` | green | CI: all scenarios pass |
| `tests-failing` | red | CI: one or more scenarios fail |

## Run Commands

```bash
npm run test:acceptance          # UI BDD (excludes @example)
npm run test:api                 # API BDD (excludes @example)
npm run test:integration         # Integration BDD (excludes @example)
npm run test:prompt-eval         # Prompt eval BDD (TS, excludes @example)
npm run test:prompt-eval:python  # Prompt eval BDD (Python/DeepEval/Ragas)
npm run test:prompt-eval:all     # Both prompt eval runners
npm run test:examples            # Run only @example template tests
npm run prompt:compare           # Side-by-side prompt comparison
npm run prompt:redteam           # Security red-teaming
npm run report:cucumber          # Cucumber report
npm run docs:serve               # Living documentation site
npm run docs:deploy              # Deploy to GitHub Pages
```

## Output Locations

- `reports/` — All test output (gitignored): cucumber, playwright, test-results, .features-gen
- `spec-web/` — Living documentation tooling: mkdocs config, build script, CSS overrides
- `spec-web/site/` + `spec-web/build/` — Generated docs (gitignored)
