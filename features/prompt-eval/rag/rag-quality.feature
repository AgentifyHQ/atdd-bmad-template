@prompt-eval @rag @P0
Feature: RAG Pipeline Quality
  As a system owner
  I want the RAG pipeline to retrieve relevant context and generate grounded answers
  So that users get accurate, source-backed responses

  # ── Faithfulness: Is the answer grounded in retrieved context? ──

  @faithfulness
  Scenario: RAG answer is faithful to retrieved context
    Given the question "What are the economic costs of climate inaction?"
    And the retrieved context:
      """
      The economic cost of inaction is estimated at $23 trillion by 2050,
      compared to $4 trillion for implementing the recommended mitigation strategies.
      """
    And the RAG answer:
      """
      According to the IPCC report, the economic cost of climate inaction is
      estimated at $23 trillion by 2050. In comparison, implementing recommended
      mitigation strategies would cost approximately $4 trillion, making proactive
      action significantly more cost-effective.
      """
    Then the faithfulness score should be >= 0.7

  # ── Answer Relevancy: Does the answer address the question? ──

  @relevancy
  Scenario: RAG answer is relevant to user question
    Given the question "What are the economic costs of climate inaction?"
    And the retrieved context:
      """
      The economic cost of inaction is estimated at $23 trillion by 2050,
      compared to $4 trillion for implementing the recommended mitigation strategies.
      """
    And the RAG answer:
      """
      According to the IPCC report, the economic cost of climate inaction is
      estimated at $23 trillion by 2050. In comparison, implementing recommended
      mitigation strategies would cost approximately $4 trillion.
      """
    Then the answer relevancy score should be >= 0.7

  # ── Context Quality: Is the retrieved context useful? ──

  @context-precision
  Scenario: Retrieved context is relevant to the question
    Given the question "What are the economic costs of climate inaction?"
    And the retrieved context:
      """
      The economic cost of inaction is estimated at $23 trillion by 2050,
      compared to $4 trillion for implementing the recommended mitigation strategies.
      """
    And the RAG answer:
      """
      Climate inaction costs $23 trillion by 2050 versus $4 trillion for mitigation.
      """
    Then the context precision score should be >= 0.6

  @context-recall
  Scenario: Retrieved context contains needed information
    Given the question "What are the economic costs of climate inaction?"
    And the retrieved context:
      """
      The economic cost of inaction is estimated at $23 trillion by 2050,
      compared to $4 trillion for implementing the recommended mitigation strategies.
      """
    And the RAG answer:
      """
      Climate inaction costs $23 trillion by 2050 versus $4 trillion for mitigation.
      """
    And the reference answer "Climate inaction costs $23 trillion by 2050. Mitigation costs $4 trillion."
    Then the context recall score should be >= 0.7

  # ── Factual Correctness: Are the facts right? ──

  @factual
  Scenario: RAG answer is factually correct against reference
    Given the question "What are the economic costs of climate inaction?"
    And the RAG answer:
      """
      Climate inaction is projected to cost $23 trillion by 2050, while
      implementing mitigation strategies would cost about $4 trillion.
      """
    And the reference answer "Climate inaction costs $23 trillion by 2050. Mitigation costs $4 trillion."
    Then the factual correctness score should be >= 0.7
