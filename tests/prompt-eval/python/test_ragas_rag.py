"""
Ragas BDD Step Definitions — RAG Pipeline Quality

Maps Gherkin steps from features/prompt-eval/rag/ to Ragas metrics.
The feature file defines WHAT RAG quality means; these steps define HOW to measure it.

Run: pytest test_ragas_rag.py -v
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from ragas import evaluate
from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
from ragas.metrics import (
    Faithfulness,
    ResponseRelevancy,
    LLMContextPrecisionWithoutReference,
    LLMContextRecall,
    FactualCorrectness,
)

# ── Load all scenarios from the shared feature file ──
scenarios("rag/rag-quality.feature")


# ──────────────────────────────────────────────
# Shared state per scenario
# ──────────────────────────────────────────────


@pytest.fixture
def rag_context():
    """Mutable context dict shared across steps within a single scenario."""
    return {
        "question": "",
        "retrieved_contexts": [],
        "rag_answer": "",
        "reference_answer": "",
    }


# ──────────────────────────────────────────────
# Given
# ──────────────────────────────────────────────


@given(parsers.parse('the question "{question}"'), target_fixture="rag_context")
def set_question(question: str, rag_context: dict) -> dict:
    rag_context["question"] = question
    return rag_context


@given("the retrieved context:")
def set_retrieved_context(rag_context: dict, docstring: str):
    rag_context["retrieved_contexts"] = [docstring.strip()]


@given("the RAG answer:")
def set_rag_answer(rag_context: dict, docstring: str):
    rag_context["rag_answer"] = docstring.strip()


@given(parsers.parse('the reference answer "{reference}"'))
def set_reference_answer(reference: str, rag_context: dict):
    rag_context["reference_answer"] = reference


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def build_sample(ctx: dict) -> SingleTurnSample:
    """Build a Ragas evaluation sample from the scenario context."""
    return SingleTurnSample(
        user_input=ctx["question"],
        response=ctx["rag_answer"],
        retrieved_contexts=ctx["retrieved_contexts"],
        reference=ctx.get("reference_answer", ""),
    )


def run_metric(ctx: dict, metric, metric_key: str) -> float:
    """Run a single Ragas metric and return the score."""
    dataset = EvaluationDataset(samples=[build_sample(ctx)])
    result = evaluate(dataset=dataset, metrics=[metric])
    return result.scores[0][metric_key]


# ──────────────────────────────────────────────
# Then: Faithfulness
# ──────────────────────────────────────────────


@then(parsers.parse("the faithfulness score should be >= {threshold:f}"))
def check_faithfulness(threshold: float, rag_context: dict):
    score = run_metric(rag_context, Faithfulness(), "faithfulness")
    assert score >= threshold, f"Faithfulness score {score:.2f} below threshold {threshold}"


# ──────────────────────────────────────────────
# Then: Answer Relevancy
# ──────────────────────────────────────────────


@then(parsers.parse("the answer relevancy score should be >= {threshold:f}"))
def check_answer_relevancy(threshold: float, rag_context: dict):
    score = run_metric(rag_context, ResponseRelevancy(), "response_relevancy")
    assert score >= threshold, f"Answer relevancy score {score:.2f} below threshold {threshold}"


# ──────────────────────────────────────────────
# Then: Context Precision
# ──────────────────────────────────────────────


@then(parsers.parse("the context precision score should be >= {threshold:f}"))
def check_context_precision(threshold: float, rag_context: dict):
    score = run_metric(
        rag_context,
        LLMContextPrecisionWithoutReference(),
        "llm_context_precision_without_reference",
    )
    assert score >= threshold, f"Context precision score {score:.2f} below threshold {threshold}"


# ──────────────────────────────────────────────
# Then: Context Recall
# ──────────────────────────────────────────────


@then(parsers.parse("the context recall score should be >= {threshold:f}"))
def check_context_recall(threshold: float, rag_context: dict):
    score = run_metric(rag_context, LLMContextRecall(), "llm_context_recall")
    assert score >= threshold, f"Context recall score {score:.2f} below threshold {threshold}"


# ──────────────────────────────────────────────
# Then: Factual Correctness
# ──────────────────────────────────────────────


@then(parsers.parse("the factual correctness score should be >= {threshold:f}"))
def check_factual_correctness(threshold: float, rag_context: dict):
    score = run_metric(rag_context, FactualCorrectness(), "factual_correctness")
    assert score >= threshold, f"Factual correctness score {score:.2f} below threshold {threshold}"
