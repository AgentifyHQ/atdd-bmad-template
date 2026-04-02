# Contract Testing with Pact

## What Is Contract Testing?

Contract testing validates API agreements between services without running them together. Instead of standing up consumer and provider simultaneously (slow, flaky, complex), each side tests independently against a shared contract.

```
Consumer (frontend/service A)          Provider (backend/service B)
─────────────────────────────          ─────────────────────────────
Defines expected requests/responses    Verifies it satisfies all contracts
Generates a "pact file" (the contract)  Runs against the pact file
Tests pass without real provider       Tests pass without real consumer
```

The contract is the handshake: "I expect this request to produce this response." If the provider changes its API in a way that breaks the contract, provider verification fails *before* deployment.

## Why Not Just Use Integration Tests?

| | Integration Tests | Contract Tests |
|---|---|---|
| **Setup** | Both services running | Each service tested alone |
| **Speed** | Slow (network, databases) | Fast (mock servers) |
| **Flakiness** | High (environment issues) | Low (deterministic) |
| **Feedback** | Late (after deployment) | Early (before merge) |
| **Ownership** | Shared, unclear | Consumer defines, provider verifies |

Contract tests don't replace integration tests — they catch a different class of bugs (API shape changes) much earlier and more reliably.

## Where Does Pact Live?

**Contract tests live in the source code repos, not in this test repo.**

This ATDD template repo tests behavior against running services. Contract testing validates the agreements *between* services at the code level. Each service repo owns its side:

| Side | Repo | What It Does |
|------|------|-------------|
| **Consumer** | The service that *calls* the API | Defines expected interactions, generates pact files |
| **Provider** | The service that *serves* the API | Verifies it satisfies all consumer contracts |

## Quick Example

### Consumer side (e.g., frontend repo)

```typescript
// tests/contract/user-api.pact.spec.ts
const provider = new PactV3({
  consumer: 'user-management-web',
  provider: 'user-api-service',
});

it('should return user when user exists', async () => {
  await provider
    .given('user with id 1 exists')           // provider state
    .uponReceiving('a request for user 1')
    .withRequest({ method: 'GET', path: '/users/1' })
    .willRespondWith({
      status: 200,
      body: like({ id: integer(1), name: string('John Doe') }),
    })
    .executeTest(async (mockServer) => {
      // Call your actual code against the mock server
      const user = await getUserById(1, { baseURL: mockServer.url });
      expect(user.name).toBe('John Doe');
    });
});
```

### Provider side (e.g., backend repo)

```typescript
// tests/contract/provider-verification.spec.ts
const verifier = new Verifier({
  providerBaseUrl: 'http://localhost:3000',
  pactUrls: ['./pacts/user-management-web-user-api-service.json'],
  stateHandlers: {
    'user with id 1 exists': async () => {
      await seedUser({ id: 1, name: 'John Doe' });
    },
  },
});

it('validates consumer contracts', () => verifier.verifyProvider());
```

## The CI Flow

```
Consumer PR                          Provider PR
───────────                          ───────────
1. Run consumer tests                1. Run provider tests
2. Generate pact file                2. Fetch pact from broker
3. Publish pact to broker            3. Verify against all consumer pacts
4. can-i-deploy? ──► Broker ◄── 4. can-i-deploy?
5. Deploy if safe                    5. Deploy if safe
```

A **Pact Broker** (or PactFlow) stores contracts and tracks verification status. The `can-i-deploy` check prevents deploying a version that would break a consumer.

## Tools & Resources

| Tool | Purpose |
|------|---------|
| [@pact-foundation/pact](https://github.com/pact-foundation/pact-js) | Core Pact.js library for consumer and provider testing |
| [PactFlow](https://pactflow.io/) | Managed Pact Broker with can-i-deploy, webhooks, and dashboards |
| [Pact MCP Server](https://github.com/SmartBear-DevRel) | SmartBear MCP for AI-assisted contract test generation |

## Getting Started in Your Service Repo

1. **Install Pact** in the service repo: `npm install -D @pact-foundation/pact`
2. **Write consumer tests** that define expected API interactions
3. **Write provider verification** that runs against the generated pact files
4. **Set up a Pact Broker** (PactFlow or self-hosted) for CI integration
5. **Add `can-i-deploy`** to your CI pipeline as a release gate

For detailed patterns, the Test Architect (`/bmad-tea`) has comprehensive Pact knowledge fragments covering consumer helpers, provider verification, dependency injection patterns, and CI framework setup.
