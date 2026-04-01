#!/usr/bin/env python3
"""
Build Living Documentation from Gherkin feature files + Cucumber JSON report.

Reads:
  - features/**/*.feature     (the specifications)
  - cucumber-report/report.json (test results, optional)

Writes:
  - docs/living-docs/site/     (markdown pages for MkDocs)
  - mkdocs.yml nav section     (auto-generated navigation)

Usage:
  python scripts/build-living-docs.py
  python scripts/build-living-docs.py --features-dir features --report cucumber-report/report.json
"""

import argparse
import json
import re
import shutil
import textwrap
from dataclasses import dataclass, field
from pathlib import Path


# ──────────────────────────────────────────────
# Data models
# ──────────────────────────────────────────────

@dataclass
class Step:
    keyword: str
    text: str
    doc_string: str = ""
    data_table: list[list[str]] = field(default_factory=list)
    status: str = ""  # passed, failed, skipped, ""
    duration_ms: float = 0
    error_message: str = ""


@dataclass
class Scenario:
    name: str
    tags: list[str] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    scenario_type: str = "scenario"  # scenario, background

    @property
    def status(self) -> str:
        statuses = [s.status for s in self.steps if s.status]
        if not statuses:
            return ""
        if any(s == "failed" for s in statuses):
            return "failed"
        if any(s == "skipped" for s in statuses):
            return "skipped"
        return "passed"


@dataclass
class Feature:
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    uri: str = ""
    background: Scenario | None = None
    scenarios: list[Scenario] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for s in self.scenarios if s.status == "passed")

    @property
    def failed_count(self) -> int:
        return sum(1 for s in self.scenarios if s.status == "failed")

    @property
    def skipped_count(self) -> int:
        return sum(1 for s in self.scenarios if s.status == "skipped")

    @property
    def no_result_count(self) -> int:
        return sum(1 for s in self.scenarios if s.status == "")


# ──────────────────────────────────────────────
# Gherkin parser (simple, no external deps)
# ──────────────────────────────────────────────

def parse_feature_file(path: Path) -> Feature:
    """Parse a .feature file into a Feature object (spec only, no results)."""
    lines = path.read_text().splitlines()
    feature = Feature(name="", uri=str(path))
    current_scenario: Scenario | None = None
    in_doc_string = False
    doc_string_lines: list[str] = []
    pending_tags: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Doc string boundaries
        if stripped.startswith('"""'):
            if in_doc_string:
                in_doc_string = False
                if current_scenario and current_scenario.steps:
                    current_scenario.steps[-1].doc_string = "\n".join(doc_string_lines)
                doc_string_lines = []
            else:
                in_doc_string = True
                doc_string_lines = []
            i += 1
            continue

        if in_doc_string:
            doc_string_lines.append(line.rstrip())
            i += 1
            continue

        # Tags
        if stripped.startswith("@"):
            pending_tags.extend(re.findall(r"@[\w-]+", stripped))
            i += 1
            continue

        # Feature
        if stripped.startswith("Feature:"):
            feature.name = stripped[len("Feature:"):].strip()
            feature.tags = pending_tags
            pending_tags = []
            # Collect description lines (skip comments)
            desc_lines = []
            i += 1
            while i < len(lines):
                next_stripped = lines[i].strip()
                if next_stripped.startswith(("Scenario", "Background", "@", "Rule:")):
                    break
                if next_stripped and not next_stripped.startswith("#"):
                    desc_lines.append(next_stripped)
                i += 1
            feature.description = "\n".join(desc_lines)
            continue

        # Background
        if stripped.startswith("Background:"):
            current_scenario = Scenario(name="Background", scenario_type="background")
            feature.background = current_scenario
            pending_tags = []
            i += 1
            continue

        # Scenario / Scenario Outline
        if stripped.startswith("Scenario Outline:") or stripped.startswith("Scenario:"):
            name = stripped.split(":", 1)[1].strip()
            current_scenario = Scenario(name=name, tags=pending_tags)
            feature.scenarios.append(current_scenario)
            pending_tags = []
            i += 1
            continue

        # Examples
        if stripped.startswith("Examples:"):
            i += 1
            continue

        # Data table rows (| col | col |)
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if current_scenario and current_scenario.steps:
                current_scenario.steps[-1].data_table.append(cells)
            i += 1
            continue

        # Steps
        step_match = re.match(r"^(Given|When|Then|And|But)\s+(.+)$", stripped)
        if step_match and current_scenario:
            keyword, text = step_match.groups()
            current_scenario.steps.append(Step(keyword=keyword, text=text))
            i += 1
            continue

        i += 1

    return feature


# ──────────────────────────────────────────────
# Cucumber JSON report loader
# ──────────────────────────────────────────────

def load_cucumber_results(report_path: Path) -> dict[str, Feature]:
    """Load cucumber JSON report and return results keyed by feature URI."""
    if not report_path.exists():
        return {}

    with open(report_path) as f:
        data = json.load(f)

    results: dict[str, list] = {}
    for feat in data:
        uri = feat.get("uri", "")
        results[uri] = feat.get("elements", [])

    return results


def merge_results(feature: Feature, elements: list[dict]) -> None:
    """Merge cucumber JSON results into a parsed Feature.

    Cucumber JSON embeds background steps inside each scenario's steps array.
    We need to skip those when matching against our parsed scenario steps
    (which don't include background steps).
    """
    # Count background steps so we can skip them in result arrays
    bg_step_count = len(feature.background.steps) if feature.background else 0

    # Build lookup: scenario name -> list of result elements
    result_map: dict[str, list[dict]] = {}
    for elem in elements:
        if elem.get("type") == "background":
            continue
        name = elem.get("name", "")
        result_map.setdefault(name, []).append(elem)

    for scenario in feature.scenarios:
        matches = result_map.get(scenario.name, [])
        if not matches:
            continue

        # Use the first matching result (handles scenario outlines with same name)
        elem = matches.pop(0)
        result_steps = elem.get("steps", [])

        # Skip background steps that cucumber embeds at the start
        scenario_result_steps = result_steps[bg_step_count:]

        for i, step in enumerate(scenario.steps):
            if i < len(scenario_result_steps):
                rs = scenario_result_steps[i]
                result = rs.get("result", {})
                step.status = result.get("status", "")
                step.duration_ms = result.get("duration", 0) / 1_000_000
                step.error_message = result.get("error_message", "")


# ──────────────────────────────────────────────
# Markdown generators
# ──────────────────────────────────────────────

def tag_html(tag: str) -> str:
    """Render a tag as styled HTML span."""
    layers = {"@acceptance", "@api", "@integration", "@prompt-eval"}
    priorities = {"@P0", "@P1", "@P2"}

    if tag in layers:
        cls = "tag tag-layer"
    elif tag in priorities:
        cls = "tag tag-priority"
    elif tag in {"@smoke", "@deterministic", "@semantic", "@llm-judge", "@faithfulness", "@rag", "@safety", "@negative"}:
        cls = "tag tag-category"
    else:
        cls = "tag tag-default"

    return f'<span class="{cls}">{tag}</span>'


def status_icon(status: str) -> str:
    if status == "passed":
        return "&#x2705;"  # green check
    elif status == "failed":
        return "&#x274C;"  # red X
    elif status == "skipped":
        return "&#x26A0;&#xFE0F;"  # warning
    return "&#x2B1C;"  # white square (no results)


def render_step(step: Step) -> str:
    """Render a single step as HTML."""
    status_cls = f"step-{step.status}" if step.status else "step-no-results"
    duration = f'<span class="step-duration">{step.duration_ms:.0f}ms</span>' if step.duration_ms else ""

    html = f'<div class="step {status_cls}">'
    html += f'<span class="step-keyword">{step.keyword}</span> {_escape(step.text)}'
    html += duration
    html += '</div>\n'

    if step.doc_string:
        html += f'<div class="step-docstring">{_escape(step.doc_string)}</div>\n'

    if step.data_table:
        html += '<div class="step-datatable"><table>\n'
        for row_i, row in enumerate(step.data_table):
            tag = "th" if row_i == 0 else "td"
            html += "<tr>" + "".join(f"<{tag}>{_escape(c)}</{tag}>" for c in row) + "</tr>\n"
        html += '</table></div>\n'

    if step.error_message:
        html += '<div class="step-error">\n'
        html += "<details>\n"
        html += "<summary>Show error details</summary>\n\n"
        html += f"```\n{step.error_message.strip()}\n```\n\n"
        html += "</details>\n"
        html += "</div>\n"

    return html


def render_scenario(scenario: Scenario) -> str:
    """Render a scenario block."""
    status_cls = f"scenario-{scenario.status}" if scenario.status else "scenario-no-results"
    icon = status_icon(scenario.status)
    tags_html = " ".join(tag_html(t) for t in scenario.tags) if scenario.tags else ""

    html = f'<div class="scenario {status_cls}" markdown>\n'
    html += f'<div class="scenario-title"><span class="status-icon">{icon}</span> {_escape(scenario.name)}</div>\n'
    if tags_html:
        html += f'<div style="margin: 0.3rem 0 0.5rem 0">{tags_html}</div>\n'

    html += "\n<details>\n<summary>Steps</summary>\n\n"
    for step in scenario.steps:
        html += render_step(step)
    html += "\n</details>\n\n"
    html += "</div>\n\n"
    return html


def _step_status_indicator(step: Step) -> str:
    """No icons — return empty string."""
    return ""


def _step_duration_badge(step: Step) -> str:
    """Duration badge for step summary line."""
    if step.duration_ms > 0:
        return f'<span class="step-duration">{step.duration_ms:.0f}ms</span>'
    return ""


def _render_step_body(step: Step) -> str:
    """Render the expanded content of a step — test output, docstrings, tables, errors."""
    html = '<div class="step-body">\n'

    # Test output info
    if step.status:
        html += '<div class="step-test-output">\n'
        status_label = step.status.upper()
        html += f'<span class="step-result-label step-result-{step.status}">{status_label}</span>'
        if step.duration_ms > 0:
            html += f' &nbsp; <span class="step-result-duration">{step.duration_ms:.0f}ms</span>'
        html += '\n</div>\n'

    # DocString content
    if step.doc_string:
        html += f'<div class="step-docstring"><pre>{_escape(step.doc_string)}</pre></div>\n'

    # Data table
    if step.data_table:
        html += '<div class="step-datatable"><table>\n'
        for row_i, row in enumerate(step.data_table):
            tag = "th" if row_i == 0 else "td"
            html += "<tr>" + "".join(f"<{tag}>{_escape(c)}</{tag}>" for c in row) + "</tr>\n"
        html += '</table></div>\n'

    # Error message
    if step.error_message:
        html += '<div class="step-error-detail">\n'
        html += f'<pre>{_escape(step.error_message.strip())}</pre>\n'
        html += '</div>\n'

    # Empty state — no test results yet
    if not step.status and not step.doc_string and not step.data_table:
        html += '<div class="step-no-output">No test results available</div>\n'

    html += '</div>\n'
    return html


def render_feature_tab(feature: Feature, depth: int = 2) -> str:
    """Render the feature spec — nested collapsibles: scenario > step > output."""
    html = ""

    # Description as user story — split into lines on As a / I want / So that
    if feature.description:
        desc = feature.description
        # Break into multiline user story format
        desc = re.sub(r'\s+(I want\b)', r'\n\1', desc)
        desc = re.sub(r'\s+(So that\b)', r'\n\1', desc)
        html += f'<div class="feature-description">{_escape(desc)}</div>\n\n'

    # Background (always visible, not collapsible)
    if feature.background:
        html += '<div class="background-block">\n'
        html += "<strong>Background:</strong>\n"
        html += '<div class="background-steps">\n'
        for step in feature.background.steps:
            html += f'<div class="step-line"><span class="step-keyword">{step.keyword}</span> {_escape(step.text)}</div>\n'
        html += '</div>\n</div>\n\n'

    # Each scenario is a collapsible <details> block
    for scenario in feature.scenarios:
        scenario_only_tags = [t for t in scenario.tags if t not in feature.tags]
        prefix = "../" * (depth + 1)
        tags_html = '<span class="scenario-tags">' + " ".join(
            f'<a href="{prefix}tags/{t.lstrip("@")}/" class="scenario-tag-link"><code>{t}</code></a>'
            for t in scenario_only_tags
        ) + '</span>' if scenario_only_tags else ""
        status_cls = f"scenario-{scenario.status}" if scenario.status else "scenario-no-results"

        html += f'<details class="scenario-details {status_cls}">\n'
        html += f'<summary><strong>Scenario: {_escape(scenario.name)}</strong>{tags_html}</summary>\n\n'

        # Each step is a nested collapsible <details>
        html += '<div class="scenario-steps">\n'
        for step in scenario.steps:
            step_line = f'<span class="step-keyword">{step.keyword}</span> {_escape(step.text)}'
            indicator = _step_status_indicator(step)
            duration = _step_duration_badge(step)
            status_step_cls = f"step-{step.status}" if step.status else "step-no-results"

            html += f'<details class="step-details {status_step_cls}">\n'
            html += f'<summary class="step-summary">{indicator} {step_line} {duration}</summary>\n'
            html += _render_step_body(step)
            html += '</details>\n'

        html += '</div>\n\n'
        html += '</details>\n\n'

    return html


def render_tests_tab(feature: Feature) -> str:
    """Render the Tests tab — steps with pass/fail coloring."""
    html = ""

    # Summary bar
    total = len(feature.scenarios)
    html += '<div class="summary-bar">\n'
    html += f'<span class="summary-badge summary-total">{total} scenarios</span>\n'
    if feature.passed_count:
        html += f'<span class="summary-badge summary-passed">{status_icon("passed")} {feature.passed_count} passed</span>\n'
    if feature.failed_count:
        html += f'<span class="summary-badge summary-failed">{status_icon("failed")} {feature.failed_count} failed</span>\n'
    if feature.skipped_count:
        html += f'<span class="summary-badge summary-skipped">{status_icon("skipped")} {feature.skipped_count} skipped</span>\n'
    if feature.no_result_count:
        html += f'<span class="summary-badge summary-total">{status_icon("")} {feature.no_result_count} no results</span>\n'
    html += '</div>\n\n'

    for scenario in feature.scenarios:
        html += render_scenario(scenario)

    return html


def _tag_link(tag: str, depth: int = 2) -> str:
    """Render a tag as a clickable link to the tag index page.
    depth = number of path segments in the page URL (mkdocs adds +1 for directory URLs).
    """
    slug = tag.lstrip("@")
    prefix = "../" * (depth + 1)  # +1 because mkdocs serves page/index.html
    return f'<a href="{prefix}tags/{slug}/" class="tag-link">{tag}</a>'


def _find_assets(features_dir: Path, rel_path: Path) -> list[Path]:
    """Find image assets for a feature file.

    Looks for an assets/ directory next to the feature file or in the parent domain dir.
    Returns list of image paths relative to features_dir.
    """
    images = []
    search_dirs = [
        features_dir / rel_path.parent / "assets",           # same dir: features/acceptance/user-management/assets/
        features_dir / rel_path.parent.parent / "assets",     # parent dir: features/acceptance/assets/
    ]
    for assets_dir in search_dirs:
        if assets_dir.is_dir():
            for img in sorted(assets_dir.iterdir()):
                if img.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'):
                    images.append(img)
    return images


def _copy_assets(images: list[Path], features_dir: Path, output_dir: Path, rel_path: Path) -> list[str]:
    """Copy image assets to output dir and return relative paths for embedding."""
    if not images:
        return []

    # Put assets next to the generated .md file
    asset_out_dir = output_dir / rel_path.parent / "assets"
    asset_out_dir.mkdir(parents=True, exist_ok=True)

    relative_paths = []
    for img in images:
        dest = asset_out_dir / img.name
        shutil.copy(img, dest)
        # ../assets/ because mkdocs serves pages as directories (page/index.html)
        relative_paths.append(f"../assets/{img.name}")

    return relative_paths


def render_feature_page(
    feature: Feature,
    rel_path: Path | None = None,
    asset_paths: list[str] | None = None,
) -> str:
    """Render a feature page — title, tags, design mockups, then feature spec."""
    depth = len(rel_path.parent.parts) if rel_path else 2
    tags_text = " &nbsp; ".join(_tag_link(t, depth) for t in feature.tags)

    md = f'<div class="feature-header" markdown>\n'
    md += f"# Feature: {_escape(feature.name)}\n\n"
    md += f'<div class="feature-tags">{tags_text}</div>\n'
    md += "</div>\n\n"

    # Expand / Collapse all buttons
    md += '<div class="toggle-buttons">\n'
    md += '<button onclick="this.closest(\'article\').querySelectorAll(\'details\').forEach(d=>d.open=true)">Expand all</button>\n'
    md += '<button onclick="this.closest(\'article\').querySelectorAll(\'details\').forEach(d=>d.open=false)">Collapse all</button>\n'
    md += '</div>\n\n'

    # Design mockups / visual references
    if asset_paths:
        md += '<div class="design-references">\n'
        md += '<h4 class="design-heading">Design References</h4>\n'
        md += '<div class="design-gallery">\n'
        for path in asset_paths:
            # Derive label from filename: login-page.png -> Login Page
            label = Path(path).stem.replace("-", " ").replace("_", " ").title()
            md += f'<figure class="design-figure">\n'
            md += f'<img src="{path}" alt="{label}">\n'
            md += f'<figcaption>{label}</figcaption>\n'
            md += f'</figure>\n'
        md += '</div>\n'
        md += '</div>\n\n'

    md += render_feature_tab(feature, depth)
    md += "\n"

    return md


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ──────────────────────────────────────────────
# Navigation builder
# ──────────────────────────────────────────────

def generate_tag_pages(
    features: list[tuple[Path, Feature]], output_dir: Path
) -> dict[str, str]:
    """Generate a page per tag listing all features/scenarios with that tag.

    Returns dict of tag_name -> page_path (relative to docs).
    """
    # Collect: tag -> list of (feature, scenario_or_none, feature_page_path)
    tag_index: dict[str, list[tuple[str, str, str, str]]] = {}

    for rel_path, feature in features:
        page_link = str(rel_path.with_suffix(".md"))

        # Feature-level tags
        for tag in feature.tags:
            tag_index.setdefault(tag, []).append(
                (feature.name, "", page_link, "feature")
            )

        # Scenario-level tags (only tags not already on feature)
        for scenario in feature.scenarios:
            for tag in scenario.tags:
                if tag not in feature.tags:
                    tag_index.setdefault(tag, []).append(
                        (feature.name, scenario.name, page_link, "scenario")
                    )

    # Generate pages
    tags_dir = output_dir / "tags"
    tags_dir.mkdir(parents=True, exist_ok=True)
    tag_pages: dict[str, str] = {}

    for tag in sorted(tag_index.keys()):
        entries = tag_index[tag]
        slug = tag.lstrip("@")
        page_path = f"tags/{slug}.md"
        tag_pages[tag] = page_path

        md = f"# {tag}\n\n"
        md += f"All features and scenarios tagged with `{tag}`.\n\n"

        # Group by feature
        by_feature: dict[str, list[tuple[str, str, str]]] = {}
        for feat_name, scen_name, link, entry_type in entries:
            by_feature.setdefault(feat_name, []).append((scen_name, link, entry_type))

        for feat_name, items in by_feature.items():
            link = items[0][1]  # all point to same feature page
            md += f"### [Feature: {feat_name}](../{link})\n\n"
            for scen_name, _, entry_type in items:
                if entry_type == "scenario" and scen_name:
                    md += f"- Scenario: {scen_name}\n"
            md += "\n"

        (tags_dir / f"{slug}.md").write_text(md)
        print(f"  Generated: {tags_dir / slug}.md")

    return tag_pages


def build_nav(features: list[tuple[Path, Feature]], tag_pages: dict[str, str] | None = None) -> list:
    """Build mkdocs nav structure from features + tag pages."""
    tree: dict = {}

    for rel_path, feature in features:
        parts = rel_path.parts
        layer = parts[0]
        domain = parts[1] if len(parts) > 2 else ""
        filename = parts[-1].replace(".feature", "")
        page_path = str(rel_path.with_suffix(".md"))

        tree.setdefault(layer, {})
        if domain:
            tree[layer].setdefault(domain, [])
            tree[layer][domain].append({_title(filename): page_path})
        else:
            tree[layer].setdefault("_pages", [])
            tree[layer]["_pages"].append({_title(filename): page_path})

    nav = [{"Home": "index.md"}]
    for layer in sorted(tree.keys()):
        layer_items: list = []
        domains = tree[layer]
        for domain in sorted(domains.keys()):
            if domain == "_pages":
                layer_items.extend(domains[domain])
            else:
                layer_items.append({_title(domain): domains[domain]})
        nav.append({_title(layer): layer_items})

    # Add Tags section
    if tag_pages:
        tag_items = []
        for tag in sorted(tag_pages.keys()):
            tag_items.append({tag: tag_pages[tag]})
        nav.append({"Tags": tag_items})

    return nav


def _title(slug: str) -> str:
    """Convert kebab-case to Title Case."""
    return slug.replace("-", " ").replace("_", " ").title()


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build living documentation")
    parser.add_argument("--features-dir", default="features", help="Path to features directory")
    parser.add_argument("--report", default="reports/cucumber/report.json", help="Path to cucumber JSON report")
    parser.add_argument("--output-dir", default="spec-web/site", help="Output directory for markdown pages")
    args = parser.parse_args()

    features_dir = Path(args.features_dir)
    report_path = Path(args.report)
    output_dir = Path(args.output_dir)

    # Clean output
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # Copy static assets
    (output_dir / "stylesheets").mkdir(exist_ok=True)
    css_src = Path("spec-web/overrides/stylesheets/living-docs.css")
    if css_src.exists():
        shutil.copy(css_src, output_dir / "stylesheets" / "living-docs.css")


    # Load cucumber results
    cucumber_results = load_cucumber_results(report_path)

    # Parse all feature files
    features: list[tuple[Path, Feature]] = []
    for feature_path in sorted(features_dir.rglob("*.feature")):
        rel_path = feature_path.relative_to(features_dir)
        feature = parse_feature_file(feature_path)
        feature.uri = str(feature_path)

        # Merge test results if available
        for uri_key, elements in cucumber_results.items():
            if uri_key == str(feature_path) or uri_key.endswith(str(rel_path)):
                merge_results(feature, elements)
                break

        features.append((rel_path, feature))

    # Generate pages
    for rel_path, feature in features:
        page_path = output_dir / rel_path.with_suffix(".md")
        page_path.parent.mkdir(parents=True, exist_ok=True)

        # Find and copy design assets
        images = _find_assets(features_dir, rel_path)
        asset_paths = _copy_assets(images, features_dir, output_dir, rel_path)

        page_path.write_text(render_feature_page(feature, rel_path, asset_paths))
        asset_note = f" (+{len(asset_paths)} images)" if asset_paths else ""
        print(f"  Generated: {page_path}{asset_note}")

    # Generate index page
    index_content = render_index(features)
    (output_dir / "index.md").write_text(index_content)
    print(f"  Generated: {output_dir / 'index.md'}")

    # Generate tag index pages
    tag_pages = generate_tag_pages(features, output_dir)
    print(f"\nTags: {len(tag_pages)} tag pages generated")

    # Generate nav
    nav = build_nav(features, tag_pages)
    print(f"\nNavigation ({len(features)} features):")
    for item in nav:
        print(f"  {item}")

    # Update mkdocs.yml nav
    update_mkdocs_nav(nav)

    print(f"\nDone. Run: mkdocs serve -f spec-web/mkdocs.yml")


def render_index(features: list[tuple[Path, Feature]]) -> str:
    """Render the landing page with summary across all features."""
    total_scenarios = sum(len(f.scenarios) for _, f in features)
    total_passed = sum(f.passed_count for _, f in features)
    total_failed = sum(f.failed_count for _, f in features)
    total_no_result = sum(f.no_result_count for _, f in features)

    md = "# Living Documentation\n\n"
    md += "Feature specifications with test results from the latest run.\n\n"

    md += '<div class="summary-bar">\n'
    md += f'<span class="summary-badge summary-total">{len(features)} features</span>\n'
    md += f'<span class="summary-badge summary-total">{total_scenarios} scenarios</span>\n'
    if total_passed:
        md += f'<span class="summary-badge summary-passed">{status_icon("passed")} {total_passed} passed</span>\n'
    if total_failed:
        md += f'<span class="summary-badge summary-failed">{status_icon("failed")} {total_failed} failed</span>\n'
    if total_no_result:
        md += f'<span class="summary-badge summary-total">{status_icon("")} {total_no_result} no results</span>\n'
    md += '</div>\n\n'

    # Features table
    md += "| Feature | Scenarios | Passed | Failed | Status |\n"
    md += "|---------|-----------|--------|--------|--------|\n"
    for rel_path, feature in features:
        link = str(rel_path.with_suffix(".md"))
        total = len(feature.scenarios)
        status = status_icon("passed") if feature.failed_count == 0 and feature.passed_count > 0 else (
            status_icon("failed") if feature.failed_count > 0 else status_icon("")
        )
        md += f"| [{feature.name}]({link}) | {total} | {feature.passed_count} | {feature.failed_count} | {status} |\n"

    return md


def update_mkdocs_nav(nav: list) -> None:
    """Update the nav section in mkdocs.yml."""
    mkdocs_path = Path("spec-web/mkdocs.yml")
    if not mkdocs_path.exists():
        return

    content = mkdocs_path.read_text()

    # Remove existing nav section
    content = re.sub(
        r"\n# Auto-generated navigation\nnav:.*?(?=\n[a-z]|\Z)",
        "",
        content,
        flags=re.DOTALL,
    )

    def _yaml_key(k: str) -> str:
        """Quote YAML keys that contain special characters."""
        if any(c in k for c in '@:#{}[]|>&*!'):
            return f'"{k}"'
        return k

    # Build nav YAML
    nav_yaml = "\n# Auto-generated navigation\nnav:\n"
    for item in nav:
        for key, value in item.items():
            if isinstance(value, str):
                nav_yaml += f"  - {_yaml_key(key)}: {value}\n"
            elif isinstance(value, list):
                nav_yaml += f"  - {_yaml_key(key)}:\n"
                for sub in value:
                    if isinstance(sub, dict):
                        for sk, sv in sub.items():
                            if isinstance(sv, str):
                                nav_yaml += f"      - {_yaml_key(sk)}: {sv}\n"
                            elif isinstance(sv, list):
                                nav_yaml += f"      - {_yaml_key(sk)}:\n"
                                for ssub in sv:
                                    if isinstance(ssub, dict):
                                        for ssk, ssv in ssub.items():
                                            nav_yaml += f"          - {_yaml_key(ssk)}: {ssv}\n"
                    elif isinstance(sub, str):
                        nav_yaml += f"      - {sub}\n"

    content = content.rstrip() + "\n" + nav_yaml
    mkdocs_path.write_text(content)
    print(f"  Updated: mkdocs.yml nav")


if __name__ == "__main__":
    main()
