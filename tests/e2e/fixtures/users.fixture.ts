/**
 * Test user fixtures
 */

export interface TestUser {
  id: string;
  email: string;
  password: string;
  name: string;
  role: 'admin' | 'user';
  is_active: boolean;
}

export const testUsers = {
  admin: {
    id: 'admin-001',
    email: 'admin@example.com',
    password: 'admin123',
    name: 'Admin User',
    role: 'admin' as const,
    is_active: true,
  },
  regularUser: {
    id: 'user-001',
    email: 'user@example.com',
    password: 'user123',
    name: 'Regular User',
    role: 'user' as const,
    is_active: true,
  },
  inactiveUser: {
    id: 'user-002',
    email: 'inactive@example.com',
    password: 'inactive123',
    name: 'Inactive User',
    role: 'user' as const,
    is_active: false,
  },
};

/**
 * Create a test user with custom values
 */
export function createUser(overrides: Partial<TestUser> = {}): TestUser {
  return {
    id: `user-${Date.now()}`,
    email: `test-${Date.now()}@example.com`,
    password: 'test123',
    name: 'Test User',
    role: 'user',
    is_active: true,
    ...overrides,
  };
}
