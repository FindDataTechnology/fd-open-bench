/**
 * Authentication utilities for e2e tests
 */

import axios from 'axios';

const API_BASE_URL = process.env.E2E_API_URL || 'http://localhost:8001/api/v1';

/**
 * Login via API and get access token
 */
export async function loginViaApi(email: string, password: string): Promise<string> {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/auth/login`,
      { email, password },
      {
        headers: {
          'Content-Type': 'application/json',
        },
        validateStatus: (status) => status < 500, // Accept all except server errors
      }
    );

    if (!response.data || !response.data.access_token) {
      throw new Error('No access token returned from login');
    }

    return response.data.access_token;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`Login failed: ${error.message}`);
    }
    throw error;
  }
}

/**
 * Get axios instance with auth token
 */
export function getAuthenticatedAxios(token: string) {
  return axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
}

/**
 * Verify user is authenticated
 */
export async function verifyAuth(token: string): Promise<boolean> {
  try {
    const response = await axios.get(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return response.status === 200;
  } catch {
    return false;
  }
}

/**
 * Create authentication session
 */
export interface AuthSession {
  token: string;
  user: {
    id: string;
    email: string;
    role: string;
  };
}

export async function createAuthSession(
  email: string,
  password: string
): Promise<AuthSession> {
  const token = await loginViaApi(email, password);

  // Decode token to get user info
  const parts = token.split('.');
  const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());

  return {
    token,
    user: {
      id: payload.sub,
      email: payload.email,
      role: payload.role,
    },
  };
}
