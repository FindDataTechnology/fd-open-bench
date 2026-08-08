/**
 * Authentication e2e tests
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { testUsers } from '../fixtures/users.fixture';

test.describe('Authentication', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test.describe('Login Flow', () => {
    test('should login successfully with valid credentials', async () => {
      // Arrange
      const { email, password } = testUsers.admin;

      // Act
      await loginPage.login(email, password);

      // Assert
      await loginPage.waitForDashboard();
      expect(await loginPage.isOnDashboard()).toBeTruthy();
    });

    test('should show error with invalid password', async () => {
      // Arrange
      const { email } = testUsers.admin;
      const invalidPassword = 'wrongpassword';

      // Act
      await loginPage.login(email, invalidPassword);

      // Assert
      await expect(loginPage.page.locator('[data-testid="error-message"]')).toBeVisible();
      expect(await loginPage.isOnLoginPage()).toBeTruthy();
    });

    test('should show error with non-existent email', async () => {
      // Arrange
      const nonExistentEmail = 'nonexistent@example.com';
      const { password } = testUsers.admin;

      // Act
      await loginPage.login(nonExistentEmail, password);

      // Assert
      await expect(loginPage.page.locator('[data-testid="error-message"]')).toBeVisible();
      expect(await loginPage.isOnLoginPage()).toBeTruthy();
    });

    test('should show validation errors for empty form', async () => {
      // Act
      await loginPage.submitEmptyForm();

      // Assert
      const emailError = await loginPage.getEmailValidationError();
      const passwordError = await loginPage.getPasswordValidationError();

      expect(emailError).toBeTruthy();
      expect(passwordError).toBeTruthy();
    });

    test('should mask password input', async () => {
      // Act
      await loginPage.enterPassword('testpassword');

      // Assert
      expect(await loginPage.isPasswordMasked()).toBeTruthy();
    });

    test('should clear password field after failed login', async () => {
      // Arrange
      const { email } = testUsers.admin;
      const invalidPassword = 'wrongpassword';

      // Act
      await loginPage.login(email, invalidPassword);

      // Assert
      const passwordValue = await loginPage.getPasswordValue();
      expect(passwordValue).toBe('');
    });
  });

  test.describe('Session Management', () => {
    test('should persist session after page refresh', async ({ page }) => {
      // Arrange - Login
      const { email, password } = testUsers.admin;
      await loginPage.login(email, password);
      await loginPage.waitForDashboard();

      // Act - Refresh page
      await page.reload();

      // Assert - Still logged in
      await loginPage.waitForDashboard();
      expect(await loginPage.isOnDashboard()).toBeTruthy();
    });

    test('should redirect to login when accessing protected route without auth', async ({ page }) => {
      // Act - Navigate to protected route
      await page.goto('/dashboard');

      // Assert - Redirected to login
      await loginPage.waitForElement('[data-testid="email-input"]');
      expect(await loginPage.isOnLoginPage()).toBeTruthy();
    });

    test('should logout successfully', async ({ page }) => {
      // Arrange - Login
      const { email, password } = testUsers.admin;
      await loginPage.login(email, password);
      await loginPage.waitForDashboard();

      // Act - Logout
      await page.click('[data-testid="logout-button"]');

      // Assert - Redirected to login
      await loginPage.waitForElement('[data-testid="email-input"]');
      expect(await loginPage.isOnLoginPage()).toBeTruthy();
    });
  });

  test.describe('Form Validation', () => {
    test('should disable login button while submitting', async ({ page }) => {
      // Arrange
      const { email, password } = testUsers.admin;

      // Act
      await loginPage.enterEmail(email);
      await loginPage.enterPassword(password);
      await loginPage.clickLogin();

      // Assert - Button should be disabled during submission
      const button = page.locator('[data-testid="login-button"]');
      await expect(button).toBeDisabled();
    });

    test('should show loading indicator during login', async ({ page }) => {
      // Arrange
      const { email, password } = testUsers.admin;

      // Act
      await loginPage.enterEmail(email);
      await loginPage.enterPassword(password);
      await loginPage.clickLogin();

      // Assert - Loading indicator should be visible
      await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should handle network errors gracefully', async ({ page }) => {
      // Arrange - Mock network failure
      await page.route('**/api/v1/auth/login', route => route.abort());

      // Act
      await loginPage.login(testUsers.admin.email, testUsers.admin.password);

      // Assert - Error message should be displayed
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    });

    test('should handle server errors gracefully', async ({ page }) => {
      // Arrange - Mock server error
      await page.route('**/api/v1/auth/login', route =>
        route.fulfill({
          status: 500,
          body: JSON.stringify({ detail: 'Internal server error' }),
        })
      );

      // Act
      await loginPage.login(testUsers.admin.email, testUsers.admin.password);

      // Assert - Error message should be displayed
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    });
  });
});
