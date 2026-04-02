#!/usr/bin/env python3
"""
Update GitHub Issue status based on test results.

Reads cucumber JSON report, finds @story-N tags on scenarios,
groups results per story, and updates the corresponding GitHub Issue:
  - All scenarios pass → label "tests-passing", move to "Done"
  - Any scenario fails → label "tests-failing", move to "In Progress"
  - No results yet    → no change

Usage:
  python scripts/update-story-status.py
  python scripts/update-story-status.py --report reports/cucumber/report.json --project 3

Requires: gh CLI authenticated with project scope
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StoryResult:
    story_id: int
    total_scenarios: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    feature_names: list[str] = field(default_factory=list)


def parse_story_results(report_path: Path) -> dict[int, StoryResult]:
    """Parse cucumber JSON and group results by @story-N tag."""
    if not report_path.exists():
        print(f"  No report found at {report_path}")
        return {}

    with open(report_path) as f:
        data = json.load(f)

    stories: dict[int, StoryResult] = {}

    for feature in data:
        feature_name = feature.get("name", "")
        feature_tags = {t["name"] for t in feature.get("tags", [])}

        # Find @story-N tags on feature
        feature_story_ids = _extract_story_ids(feature_tags)

        for element in feature.get("elements", []):
            if element.get("type") == "background":
                continue

            # Combine feature + scenario tags
            scenario_tags = {t["name"] for t in element.get("tags", [])}
            all_tags = feature_tags | scenario_tags
            story_ids = _extract_story_ids(all_tags)

            if not story_ids:
                continue

            # Determine scenario status
            steps = element.get("steps", [])
            step_statuses = [s.get("result", {}).get("status", "") for s in steps]
            if any(s == "failed" for s in step_statuses):
                status = "failed"
            elif all(s == "passed" for s in step_statuses):
                status = "passed"
            else:
                status = "skipped"

            # Record result for each linked story
            for sid in story_ids:
                if sid not in stories:
                    stories[sid] = StoryResult(story_id=sid)
                story = stories[sid]
                story.total_scenarios += 1
                if status == "passed":
                    story.passed += 1
                elif status == "failed":
                    story.failed += 1
                else:
                    story.skipped += 1
                if feature_name not in story.feature_names:
                    story.feature_names.append(feature_name)

    return stories


def _extract_story_ids(tags: set[str]) -> list[int]:
    """Extract story IDs from @story-N tags."""
    ids = []
    for tag in tags:
        match = re.match(r"@story-(\d+)", tag)
        if match:
            ids.append(int(match.group(1)))
    return ids


def update_issue_labels(story: StoryResult, repo: str, dry_run: bool = False) -> None:
    """Update GitHub Issue labels based on test results."""
    if story.failed > 0:
        new_label = "tests-failing"
        remove_label = "tests-passing"
    elif story.passed > 0 and story.failed == 0:
        new_label = "tests-passing"
        remove_label = "tests-failing"
    else:
        return  # No results, skip

    print(f"  Issue #{story.story_id}: {story.passed}/{story.total_scenarios} passed → {new_label}")

    if dry_run:
        print(f"    [dry-run] Would set label: {new_label}")
        return

    # Add new label
    _gh(["issue", "edit", str(story.story_id), "--add-label", new_label, "-R", repo])
    # Remove old label (ignore error if not present)
    _gh(["issue", "edit", str(story.story_id), "--remove-label", remove_label, "-R", repo],
        ignore_errors=True)


def update_project_status(
    story: StoryResult,
    repo: str,
    org: str,
    project_number: int,
    dry_run: bool = False,
) -> None:
    """Move issue on project board based on test results."""
    if story.failed > 0:
        new_status = "In Progress"
    elif story.passed > 0 and story.failed == 0:
        new_status = "Done"
    else:
        return

    if dry_run:
        print(f"    [dry-run] Would move to: {new_status}")
        return

    # Find the project item ID for this issue
    item_id = _find_project_item(org, project_number, repo, story.story_id)
    if not item_id:
        print(f"    Issue #{story.story_id} not found on project board — skipping column move")
        return

    # Get project ID and status field ID
    project_id = _get_project_id(org, project_number)
    status_field_id = _get_status_field_id(org, project_number)
    option_id = _get_status_option_id(org, project_number, new_status)

    if not all([project_id, status_field_id, option_id]):
        print(f"    Could not resolve project/field/option IDs — skipping column move")
        return

    # Update the status
    _gh_graphql("""
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId
            itemId: $itemId
            fieldId: $fieldId
            value: { singleSelectOptionId: $optionId }
          }) {
            projectV2Item { id }
          }
        }
    """, projectId=project_id, itemId=item_id, fieldId=status_field_id, optionId=option_id)

    print(f"    Moved to: {new_status}")


def _find_project_item(org: str, project_number: int, repo: str, issue_number: int) -> str | None:
    """Find the project item ID for a given issue."""
    result = _gh_graphql("""
        query($org: String!, $projectNumber: Int!) {
          organization(login: $org) {
            projectV2(number: $projectNumber) {
              items(first: 100) {
                nodes {
                  id
                  content {
                    ... on Issue {
                      number
                      repository { nameWithOwner }
                    }
                  }
                }
              }
            }
          }
        }
    """, org=org, projectNumber=project_number)

    items = (result.get("data", {})
             .get("organization", {})
             .get("projectV2", {})
             .get("items", {})
             .get("nodes", []))

    for item in items:
        content = item.get("content", {})
        if (content and
            content.get("number") == issue_number and
            content.get("repository", {}).get("nameWithOwner", "") == repo):
            return item["id"]

    return None


def _get_project_id(org: str, project_number: int) -> str | None:
    result = _gh_graphql("""
        query($org: String!, $n: Int!) {
          organization(login: $org) { projectV2(number: $n) { id } }
        }
    """, org=org, n=project_number)
    return result.get("data", {}).get("organization", {}).get("projectV2", {}).get("id")


def _get_status_field_id(org: str, project_number: int) -> str | None:
    result = _gh_graphql("""
        query($org: String!, $n: Int!) {
          organization(login: $org) {
            projectV2(number: $n) {
              field(name: "Status") { ... on ProjectV2SingleSelectField { id } }
            }
          }
        }
    """, org=org, n=project_number)
    return (result.get("data", {}).get("organization", {})
            .get("projectV2", {}).get("field", {}).get("id"))


def _get_status_option_id(org: str, project_number: int, status_name: str) -> str | None:
    result = _gh_graphql("""
        query($org: String!, $n: Int!) {
          organization(login: $org) {
            projectV2(number: $n) {
              field(name: "Status") {
                ... on ProjectV2SingleSelectField {
                  options { id name }
                }
              }
            }
          }
        }
    """, org=org, n=project_number)
    options = (result.get("data", {}).get("organization", {})
               .get("projectV2", {}).get("field", {}).get("options", []))
    for opt in options:
        if opt["name"] == status_name:
            return opt["id"]
    return None


def _gh(args: list[str], ignore_errors: bool = False) -> str:
    """Run gh CLI command."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True, text=True, check=not ignore_errors
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"    gh error: {e.stderr.strip()}")
        return ""


def _gh_graphql(query: str, **variables) -> dict:
    """Run gh GraphQL query."""
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if isinstance(value, int):
            args.extend(["-F", f"{key}={value}"])
        else:
            args.extend(["-f", f"{key}={value}"])

    result = subprocess.run(
        ["gh"] + args,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"    GraphQL error: {result.stderr.strip()}")
        return {}
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description="Update story status from test results")
    parser.add_argument("--report", default="reports/cucumber/report.json")
    parser.add_argument("--repo", default=None, help="owner/repo (auto-detected if in git repo)")
    parser.add_argument("--org", default="AgentifyHQ")
    parser.add_argument("--project", type=int, default=3, help="GitHub Project number")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without making changes")
    args = parser.parse_args()

    # Auto-detect repo
    repo = args.repo
    if not repo:
        try:
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                capture_output=True, text=True, check=True
            )
            repo = result.stdout.strip()
        except subprocess.CalledProcessError:
            print("Could not detect repo. Use --repo owner/name")
            sys.exit(1)

    print(f"Updating story status from: {args.report}")
    print(f"Repo: {repo} | Project: #{args.project} | Dry run: {args.dry_run}")
    print()

    # Parse results
    stories = parse_story_results(Path(args.report))
    if not stories:
        print("No @story-N tags found in test results.")
        return

    print(f"Found {len(stories)} stories with test results:")
    for story_id, result in sorted(stories.items()):
        status = "PASS" if result.failed == 0 and result.passed > 0 else "FAIL"
        print(f"  @story-{story_id}: {result.passed}/{result.total_scenarios} passed [{status}]")
        print(f"    Features: {', '.join(result.feature_names)}")

    print()

    # Update issues
    for story_id, result in sorted(stories.items()):
        update_issue_labels(result, repo, dry_run=args.dry_run)
        update_project_status(result, repo, args.org, args.project, dry_run=args.dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
