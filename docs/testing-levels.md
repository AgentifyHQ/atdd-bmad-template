# Testing Levels: What Lives Where

## The Testing Pyramid

```
          ╱╲
         ╱E2E╲              This repo: acceptance, visual regression
        ╱──────╲
       ╱  API   ╲           This repo: API behavior, prompt eval
      ╱──────────╲
     ╱ Contract   ╲         Code repos: Pact consumer + provider
    ╱──────────────╲
   ╱  Integration   ╲       Code repos: DB, services, middleware
  ╱──────────────────╲
 ╱    Unit Tests      ╲     Code repos: pure logic, no dependencies
╱──────────────────────╲
```

This template repo covers the **top layers** — testing behavior against running services. The bottom layers live in the source code repos alongside the implementation.

## Where Each Level Lives

| Level | Where | Tests What | Example |
|-------|-------|-----------|---------|
| **Unit** | Code repo | Pure functions, business logic, calculations | `calculateDiscount(100, 20)` returns `80` |
| **Developer Integration** | Code repo | DB operations, service interactions, middleware | `UserService.create()` persists to DB and assigns roles |
| **Contract** | Code repo | API shape agreements between services | Consumer expects `GET /users/1` returns `{ id, name, email }` |
| **API / Integration** | This repo | API behavior against running services | `POST /api/users` returns 201 with correct body |
| **Acceptance / E2E** | This repo | User journeys through the UI | Login → dashboard → place order |
| **Prompt Eval** | This repo | LLM output quality gates | Summary is faithful, passes rubric, no banned content |

## Unit Tests (Code Repo)

**When:** Testing pure logic with no external dependencies.

Unit tests are the foundation — fast (milliseconds), reliable (no flakiness), and cheap to maintain. They should be the bulk of your test suite.

**Good candidates for unit tests:**
- Business logic (pricing, discounts, validation rules)
- Data transformations and formatters
- State machines and workflow logic
- Input validation and sanitization
- Algorithm correctness

**Not candidates for unit tests:**
- Database queries (use integration tests)
- API endpoint behavior (use API tests)
- UI rendering (use component or E2E tests)

```typescript
// src/utils/price-calculator.test.ts
describe('calculateDiscount', () => {
  it('applies percentage discount', () => {
    expect(calculateDiscount(100, { type: 'percentage', value: 20 })).toBe(80);
  });

  it('does not go below zero', () => {
    expect(calculateDiscount(10, { type: 'fixed', value: 20 })).toBe(0);
  });
});
```

**Tools:** Jest, Vitest, pytest, Go test, JUnit — whatever your code repo uses.

## Developer Integration Tests (Code Repo)

**When:** Testing component interactions — your code talking to a database, another service, or middleware.

These run against real (or containerized) dependencies. Slower than unit tests, but they catch bugs that mocks hide — like broken SQL queries, incorrect transaction handling, or middleware ordering.

**Good candidates:**
- Database CRUD operations and constraints
- Service layer methods that coordinate multiple components  
- Middleware and interceptor behavior
- Authentication and authorization flows
- Message queue producers and consumers

```typescript
// tests/integration/user-service.test.ts
describe('UserService', () => {
  it('creates user with role and persists to DB', async () => {
    const user = await userService.create({ email: 'test@example.com', role: 'admin' });
    
    expect(user.id).toBeTruthy();
    expect(user.role).toBe('admin');
    
    // Verify DB state directly
    const row = await db.query('SELECT * FROM users WHERE id = $1', [user.id]);
    expect(row.role).toBe('admin');
    expect(row.permissions).toContain('user:delete');
  });

  it('rejects duplicate email', async () => {
    await userService.create({ email: 'dup@example.com', role: 'user' });
    
    await expect(
      userService.create({ email: 'dup@example.com', role: 'user' })
    ).rejects.toThrow('Email already exists');
  });
});
```

**Tools:** Same test runner as unit tests, plus testcontainers, in-memory databases, or Docker Compose for dependencies.

## Contract Tests (Code Repo)

**When:** Multiple services communicate via APIs and you need to prevent breaking changes without running everything together.

See [Contract Testing with Pact](contract-testing.md) for the full guide. Key points:

- **Start contract tests when** you have 2+ services with an API boundary
- **Consumer side** defines expected interactions, generates pact files
- **Provider side** verifies it satisfies all consumer contracts
- **`can-i-deploy`** gates releases — no deploying a version that breaks a consumer

Contract tests catch a specific class of bugs: "service A changed its response shape and service B doesn't know yet." Integration tests miss this because they test each service in isolation.

## How These Relate to This Repo

This test repo validates behavior **from the outside** — it hits running services and checks observable outcomes. The code repo tests validate behavior **from the inside** — they test implementation details with direct access to code, databases, and internal APIs.

```
Code Repo Tests                    This Repo Tests
(inside the system)                (outside the system)
───────────────────                ───────────────────
Unit: calculateDiscount(100,20)    API: POST /api/orders → 201
Integration: DB.insert(user)       Acceptance: User clicks "Buy" → "Order Confirmed"
Contract: Pact consumer/provider   Integration: Order service → Inventory service
                                   Prompt Eval: LLM output meets quality rubric
```

Both are needed. Neither replaces the other.

## When to Start Each Level

| Level | Start When... |
|-------|--------------|
| **Unit** | You write your first function with logic worth testing |
| **Developer Integration** | Your code touches a database, API, or external service |
| **Contract** | Two or more services communicate via API and are deployed independently |
| **API (this repo)** | A service has a public API that consumers depend on |
| **Acceptance (this repo)** | Users interact with the system through a UI |
| **Prompt Eval (this repo)** | Your system uses LLMs and you need quality guarantees |

## The Duplicate Coverage Guard

Before adding a test, ask:

1. Is this already tested at a lower level?
2. Can a unit test cover this instead of integration?
3. Can an integration test cover this instead of E2E?

Overlap is acceptable only for **critical paths** (defense in depth) or when testing **different aspects** at each level (unit: logic correctness, integration: data flow, E2E: user experience).
