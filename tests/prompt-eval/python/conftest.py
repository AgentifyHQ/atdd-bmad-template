"""
Shared fixtures and configuration for BDD prompt evaluation tests.
pytest-bdd reads feature files from features/prompt-eval/ (configured in pyproject.toml).
"""

from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env from repo root
REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env")


@pytest.fixture(scope="session")
def datasets_dir() -> Path:
    """Path to shared test datasets (reused across promptfoo and Python)."""
    return REPO_ROOT / "tests" / "prompt-eval" / "promptfoo" / "datasets"


@pytest.fixture(scope="session")
def prompts_dir() -> Path:
    """Path to shared prompt templates."""
    return REPO_ROOT / "tests" / "prompt-eval" / "promptfoo" / "prompts"


def generate_llm_output(prompt: str) -> str:
    """
    Call your LLM to generate output.
    Replace this with your actual LLM call.
    """
    # TODO: Replace with actual LLM API call
    # Example with Anthropic:
    #
    # from anthropic import Anthropic
    # client = Anthropic()
    # response = client.messages.create(
    #     model="claude-sonnet-4-6",
    #     max_tokens=1024,
    #     messages=[{"role": "user", "content": prompt}],
    # )
    # return response.content[0].text

    # Placeholder for scaffolding
    return (
        "The IPCC's March 2026 report indicates global temperatures have risen "
        "1.2 degrees Celsius since pre-industrial times, with projections to exceed "
        "1.5 degrees by 2030 without emission cuts. Extreme weather events increased "
        "15%, and the energy sector accounts for 73% of greenhouse gas emissions. "
        "Recommended actions include renewable energy transition, carbon capture, and "
        "international agreements. The 1.5-degree target remains achievable if "
        "emissions peak before 2027 and decline 43% by 2030."
    )


def generate_rag_answer(question: str, contexts: list[str]) -> str:
    """
    Call your RAG pipeline to generate an answer.
    Replace this with your actual RAG call.
    """
    # TODO: Replace with actual RAG pipeline call
    # Placeholder
    return (
        "According to the IPCC report, the economic cost of climate inaction is "
        "estimated at $23 trillion by 2050. In comparison, implementing recommended "
        "mitigation strategies would cost approximately $4 trillion, making proactive "
        "action significantly more cost-effective."
    )
