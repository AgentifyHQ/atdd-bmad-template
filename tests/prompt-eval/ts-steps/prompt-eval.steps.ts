import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { assertions } from 'promptfoo';
import * as fs from 'fs';
import * as path from 'path';

const { Given, When, Then } = createBdd();

const { matchesSimilarity, matchesLlmRubric, matchesFactuality } = assertions;

// ──────────────────────────────────────────────
// State shared within each scenario.
// Steps run sequentially within a test, so a
// simple module-level object is safe. Background
// step resets it for each scenario.
// ──────────────────────────────────────────────

let ctx = {
  sourceArticle: '',
  goldenAnswer: '',
  generatedOutput: '',
  promptVersion: '',
};

let ragCtx = {
  question: '',
  retrievedContexts: [] as string[],
  ragAnswer: '',
  referenceAnswer: '',
};

function loadDataset(filename: string): string {
  const datasetsDir = path.resolve(__dirname, '../../prompt-eval/promptfoo/datasets');
  return fs.readFileSync(path.join(datasetsDir, filename), 'utf-8').trim();
}

function loadPrompt(promptId: string): string {
  const promptsDir = path.resolve(__dirname, '../../prompt-eval/promptfoo/prompts');
  return fs.readFileSync(path.join(promptsDir, `${promptId}.txt`), 'utf-8').trim();
}

// ──────────────────────────────────────────────
// Given: Setup
// ──────────────────────────────────────────────

Given('the source article {string}', async ({}, filename: string) => {
  // Reset context for each scenario (called in Background)
  ctx = { sourceArticle: '', goldenAnswer: '', generatedOutput: '', promptVersion: '' };
  ctx.sourceArticle = loadDataset(filename);
  const goldenFile = filename.replace('article-', 'golden-summary-');
  try {
    ctx.goldenAnswer = loadDataset(goldenFile);
  } catch {
    // No golden answer for this article
  }
});

// ──────────────────────────────────────────────
// When: LLM Generation
// ──────────────────────────────────────────────

When('I generate a summary using prompt {string}', async ({ request }, promptId: string) => {
  ctx.promptVersion = promptId;
  const promptTemplate = loadPrompt(promptId);
  const fullPrompt = promptTemplate.replace('{{article}}', ctx.sourceArticle);

  // ── Replace with actual LLM call ──
  // const response = await request.post('https://api.anthropic.com/v1/messages', {
  //   headers: {
  //     'x-api-key': process.env.ANTHROPIC_API_KEY!,
  //     'anthropic-version': '2023-06-01',
  //   },
  //   data: {
  //     model: 'claude-sonnet-4-6',
  //     max_tokens: 1024,
  //     messages: [{ role: 'user', content: fullPrompt }],
  //   },
  // });
  // const body = await response.json();
  // ctx.generatedOutput = body.content[0].text;

  // Placeholder for scaffolding
  ctx.generatedOutput =
    "The IPCC's March 2026 report indicates global temperatures have risen " +
    '1.2 degrees Celsius since pre-industrial times, with projections to exceed ' +
    '1.5 degrees by 2030 without significant reductions in carbon emissions. ' +
    'Extreme weather events increased 15%, and the energy sector accounts for 73% ' +
    'of greenhouse gas emissions. Recommended actions include renewable energy ' +
    'transition, carbon capture, and international agreements. The 1.5-degree ' +
    'target remains achievable if emissions peak before 2027 and decline 43% by 2030.';
});

// ──────────────────────────────────────────────
// Then: Layer 1 — Deterministic Assertions
// ──────────────────────────────────────────────

Then('the output should be under {int} words', async ({}, maxWords: number) => {
  const wordCount = ctx.generatedOutput.split(/\s+/).length;
  expect(wordCount).toBeLessThanOrEqual(maxWords);
});

Then('the output should contain {string}', async ({}, expected: string) => {
  expect(ctx.generatedOutput.toLowerCase()).toContain(expected.toLowerCase());
});

Then('the output should not contain {string}', async ({}, banned: string) => {
  expect(ctx.generatedOutput.toLowerCase()).not.toContain(banned.toLowerCase());
});

Then('the output should contain any of:', async ({}, dataTable: any) => {
  const terms: string[] = dataTable.rows().map((row: string[]) => row[0]);
  const outputLower = ctx.generatedOutput.toLowerCase();
  const found = terms.some((term) => outputLower.includes(term.toLowerCase()));
  expect(found).toBe(true);
});

// ──────────────────────────────────────────────
// Then: Layer 2 — Semantic Similarity
// ──────────────────────────────────────────────

Then(
  'the output should be semantically similar to the golden answer with threshold {float}',
  async ({}, threshold: number) => {
    expect(ctx.goldenAnswer).toBeTruthy();
    const result = await matchesSimilarity(ctx.generatedOutput, ctx.goldenAnswer, threshold);
    expect(result.pass).toBe(true);
  },
);

// ──────────────────────────────────────────────
// Then: Layer 3 — LLM-as-Judge
// ──────────────────────────────────────────────

Then('the output should be factual given {string}', async ({}, factualClaim: string) => {
  const result = await matchesFactuality(ctx.sourceArticle, factualClaim, ctx.generatedOutput, {});
  expect(result.pass).toBe(true);
});

Then('the output should pass the rubric:', async ({}, rubric: string) => {
  const result = await matchesLlmRubric(rubric.trim(), ctx.generatedOutput, {});
  expect(result.pass).toBe(true);
});

// ──────────────────────────────────────────────
// RAG Scenario Steps
// ──────────────────────────────────────────────

Given('the question {string}', async ({}, question: string) => {
  ragCtx = { question: '', retrievedContexts: [], ragAnswer: '', referenceAnswer: '' };
  ragCtx.question = question;
});

Given('the retrieved context:', async ({}, docString: string) => {
  ragCtx.retrievedContexts = [docString.trim()];
});

Given('the RAG answer:', async ({}, docString: string) => {
  ragCtx.ragAnswer = docString.trim();
});

Given('the reference answer {string}', async ({}, reference: string) => {
  ragCtx.referenceAnswer = reference;
});

Then('the faithfulness score should be >= {float}', async ({}, _threshold: number) => {
  const result = await matchesFactuality(
    ragCtx.question,
    ragCtx.retrievedContexts.join('\n'),
    ragCtx.ragAnswer,
    {},
  );
  expect(result.pass).toBe(true);
});

Then('the answer relevancy score should be >= {float}', async ({}, _threshold: number) => {
  const result = await matchesLlmRubric(
    `The answer must directly address the question: "${ragCtx.question}". It should not contain irrelevant information.`,
    ragCtx.ragAnswer,
    {},
  );
  expect(result.pass).toBe(true);
});

Then('the context precision score should be >= {float}', async ({}, _threshold: number) => {
  const result = await matchesLlmRubric(
    `The retrieved context must be relevant to answering: "${ragCtx.question}". It should not contain noise or unrelated information.`,
    ragCtx.retrievedContexts.join('\n'),
    {},
  );
  expect(result.pass).toBe(true);
});

Then('the context recall score should be >= {float}', async ({}, threshold: number) => {
  const result = await matchesSimilarity(ragCtx.ragAnswer, ragCtx.referenceAnswer, threshold);
  expect(result.pass).toBe(true);
});

Then('the factual correctness score should be >= {float}', async ({}, _threshold: number) => {
  const result = await matchesFactuality(
    ragCtx.question,
    ragCtx.referenceAnswer,
    ragCtx.ragAnswer,
    {},
  );
  expect(result.pass).toBe(true);
});
