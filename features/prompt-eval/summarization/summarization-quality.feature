@example @prompt-eval @P0
Feature: Summarization Prompt Quality
  As a product owner
  I want the summarization prompt to produce faithful, concise summaries
  So that users receive accurate information without hallucination

  Background:
    Given the source article "article-climate.txt"

  # ── Layer 1: Deterministic (free, fast, always run) ──

  @deterministic @smoke
  Scenario: Summary respects word count limit
    When I generate a summary using prompt "summarize-v1"
    Then the output should be under 200 words

  @deterministic
  Scenario: Summary captures key domain terms
    When I generate a summary using prompt "summarize-v1"
    Then the output should contain "carbon emissions"
    And the output should contain any of:
      | term              |
      | greenhouse        |
      | climate change    |
      | global warming    |

  @deterministic @safety
  Scenario: Summary does not leak sensitive patterns
    When I generate a summary using prompt "summarize-v1"
    Then the output should not contain "SSN"
    And the output should not contain "social security"

  # ── Layer 2: Semantic Similarity (cheap, run on PR) ──

  @semantic
  Scenario: Summary stays semantically close to golden answer
    When I generate a summary using prompt "summarize-v1"
    Then the output should be semantically similar to the golden answer with threshold 0.7

  @semantic
  Scenario: Concise prompt variant preserves meaning
    When I generate a summary using prompt "summarize-v2"
    Then the output should be semantically similar to the golden answer with threshold 0.65

  # ── Layer 3: LLM-as-Judge (moderate cost, run on PR) ──

  @llm-judge
  Scenario: Summary is factually grounded in source
    When I generate a summary using prompt "summarize-v1"
    Then the output should be factual given "rising global temperatures and carbon emission targets"

  @llm-judge
  Scenario: Summary meets editorial quality rubric
    When I generate a summary using prompt "summarize-v1"
    Then the output should pass the rubric:
      """
      The summary must:
      1. Accurately represent the source article without hallucination
      2. Be written in a neutral, professional tone
      3. Not introduce claims not present in the original text
      4. Include quantitative data from the source where relevant
      """

  @llm-judge
  Scenario: Summary meets conciseness rubric
    When I generate a summary using prompt "summarize-v2"
    Then the output should pass the rubric:
      """
      The summary must:
      1. Be notably shorter than the source while preserving all key findings
      2. Avoid filler words, hedging, or unnecessary preamble
      3. Read as a single cohesive paragraph, not bullet points
      """
