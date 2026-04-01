"""
DeepEval BDD Step Definitions — Summarization Quality

Maps Gherkin steps from features/prompt-eval/summarization/ to DeepEval metrics.
The feature file defines WHAT quality means; these steps define HOW to measure it.

Run: pytest test_deepeval_faithfulness.py -v
"""

from pathlib import Path

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    GEval,
    HallucinationMetric,
)
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from conftest import generate_llm_output

# ── Load all scenarios from the shared feature files ──
scenarios("summarization/summarization-quality.feature")

# ──────────────────────────────────────────────
# Shared state per scenario
# ──────────────────────────────────────────────


@pytest.fixture
def eval_context():
    """Mutable context dict shared across steps within a single scenario."""
    return {
        "source_article": "",
        "golden_answer": "",
        "generated_output": "",
        "prompt_version": "",
    }


# ──────────────────────────────────────────────
# Given
# ──────────────────────────────────────────────


@given(parsers.parse('the source article "{filename}"'), target_fixture="eval_context")
def load_source_article(filename: str, datasets_dir: Path, eval_context: dict) -> dict:
    eval_context["source_article"] = (datasets_dir / filename).read_text().strip()
    # Try loading golden answer
    golden_file = filename.replace("article-", "golden-summary-")
    golden_path = datasets_dir / golden_file
    if golden_path.exists():
        eval_context["golden_answer"] = golden_path.read_text().strip()
    return eval_context


# ──────────────────────────────────────────────
# When
# ──────────────────────────────────────────────


@when(parsers.parse('I generate a summary using prompt "{prompt_id}"'))
def generate_summary(prompt_id: str, prompts_dir: Path, eval_context: dict):
    eval_context["prompt_version"] = prompt_id
    prompt_template = (prompts_dir / f"{prompt_id}.txt").read_text().strip()
    full_prompt = prompt_template.replace("{{article}}", eval_context["source_article"])
    eval_context["generated_output"] = generate_llm_output(full_prompt)


# ──────────────────────────────────────────────
# Then: Deterministic (Layer 1)
# ──────────────────────────────────────────────


@then(parsers.parse("the output should be under {max_words:d} words"))
def check_word_count(max_words: int, eval_context: dict):
    word_count = len(eval_context["generated_output"].split())
    assert word_count <= max_words, f"Output has {word_count} words, exceeds {max_words}"


@then(parsers.parse('the output should contain "{expected}"'))
def check_contains(expected: str, eval_context: dict):
    assert expected.lower() in eval_context["generated_output"].lower(), (
        f"Output does not contain '{expected}'"
    )


@then(parsers.parse('the output should not contain "{banned}"'))
def check_not_contains(banned: str, eval_context: dict):
    assert banned.lower() not in eval_context["generated_output"].lower(), (
        f"Output contains banned pattern '{banned}'"
    )


@then("the output should contain any of:")
def check_contains_any(eval_context: dict, datatable):
    output_lower = eval_context["generated_output"].lower()
    terms = [row[0] for row in datatable]
    found = any(term.lower() in output_lower for term in terms)
    assert found, f"Output does not contain any of: {terms}"


# ──────────────────────────────────────────────
# Then: Semantic Similarity (Layer 2)
# ── Handled by TS/promptfoo side ──
# These steps are tagged @semantic and run via playwright-bdd
# pytest-bdd will skip scenarios with unimplemented steps
# ──────────────────────────────────────────────


@then(parsers.parse(
    "the output should be semantically similar to the golden answer with threshold {threshold:f}"
))
def check_semantic_similarity(threshold: float, eval_context: dict):
    """
    Semantic similarity via DeepEval's GEval as a proxy.
    For true embedding similarity, use the TS/promptfoo steps instead.
    """
    similarity = GEval(
        name="Semantic Similarity",
        criteria=(
            "Determine if the actual output conveys the same key information "
            "as the expected output, even if worded differently."
        ),
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        threshold=threshold,
    )

    test_case = LLMTestCase(
        input="Summarize the article",
        actual_output=eval_context["generated_output"],
        expected_output=eval_context["golden_answer"],
    )

    assert_test(test_case, [similarity])


# ──────────────────────────────────────────────
# Then: LLM-as-Judge (Layer 3)
# ──────────────────────────────────────────────


@then(parsers.parse('the output should be factual given "{factual_claim}"'))
def check_factuality(factual_claim: str, eval_context: dict):
    faithfulness = FaithfulnessMetric(threshold=0.7)

    test_case = LLMTestCase(
        input="Summarize this article",
        actual_output=eval_context["generated_output"],
        retrieval_context=[eval_context["source_article"]],
    )

    assert_test(test_case, [faithfulness])


@then("the output should pass the rubric:")
def check_rubric(eval_context: dict, docstring: str):
    rubric = GEval(
        name="Quality Rubric",
        criteria=docstring.strip(),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7,
    )

    test_case = LLMTestCase(
        input="Summarize the article",
        actual_output=eval_context["generated_output"],
    )

    assert_test(test_case, [rubric])
