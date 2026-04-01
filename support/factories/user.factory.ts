/**
 * Data factories for test data generation.
 * Pure functions with sensible defaults — override only what matters per test.
 */

type UserInput = {
  name?: string;
  email?: string;
  role?: 'user' | 'admin' | 'viewer';
  password?: string;
};

let counter = 0;

export function createUser(overrides: UserInput = {}): Required<UserInput> {
  counter++;
  const uniqueId = `${Date.now()}-${counter}`;

  return {
    name: overrides.name ?? `Test User ${counter}`,
    email: overrides.email ?? `testuser-${uniqueId}@test.example.com`,
    role: overrides.role ?? 'user',
    password: overrides.password ?? 'TestPassword123!',
  };
}

export function createAdminUser(overrides: UserInput = {}): Required<UserInput> {
  return createUser({ role: 'admin', ...overrides });
}
