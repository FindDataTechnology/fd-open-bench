import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Login page object
 */
export class LoginPage extends BasePage {
  // Selectors
  private readonly emailInput = '[data-testid="email-input"]';
  private readonly passwordInput = '[data-testid="password-input"]';
  private readonly loginButton = '[data-testid="login-button"]';
  private readonly errorMessage = '[data-testid="error-message"]';
  private readonly dashboardHeading = 'h1:has-text("Dashboard")';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to login page
   */
  async goto(): Promise<void> {
    await this.navigateTo('/login');
  }

  /**
   * Enter email
   */
  async enterEmail(email: string): Promise<void> {
    await this.fillInput(this.emailInput, email);
  }

  /**
   * Enter password
   */
  async enterPassword(password: string): Promise<void> {
    await this.fillInput(this.passwordInput, password);
  }

  /**
   * Click login button
   */
  async clickLogin(): Promise<void> {
    await this.clickElement(this.loginButton);
  }

  /**
   * Wait for dashboard to load
   */
  async waitForDashboard(): Promise<void> {
    await this.waitForElement(this.dashboardHeading, 15000);
  }

  /**
   * Login with credentials
   */
  async login(email: string, password: string): Promise<void> {
    await this.enterEmail(email);
    await this.enterPassword(password);
    await this.clickLogin();
  }

  /**
   * Get error message text
   */
  async getErrorMessage(): Promise<string> {
    return await this.getTextContent(this.errorMessage);
  }

  /**
   * Check if error message is visible
   */
  async isErrorVisible(): Promise<boolean> {
    return await this.isElementVisible(this.errorMessage);
  }

  /**
   * Check if on login page
   */
  async isOnLoginPage(): Promise<boolean> {
    const url = await this.getCurrentUrl();
    return url.includes('/login');
  }

  /**
   * Check if on dashboard page
   */
  async isOnDashboard(): Promise<boolean> {
    const url = await this.getCurrentUrl();
    return url.includes('/dashboard') || url === 'http://localhost:3001/';
  }

  /**
   * Get email input value
   */
  async getEmailValue(): Promise<string> {
    return await this.getInputValue(this.emailInput);
  }

  /**
   * Get password input value
   */
  async getPasswordValue(): Promise<string> {
    return await this.getInputValue(this.passwordInput);
  }

  /**
   * Check if password is masked
   */
  async isPasswordMasked(): Promise<boolean> {
    const type = await this.getAttribute(this.passwordInput, 'type');
    return type === 'password';
  }

  /**
   * Submit empty form
   */
  async submitEmptyForm(): Promise<void> {
    await this.clickLogin();
  }

  /**
   * Get validation error for email
   */
  async getEmailValidationError(): Promise<string> {
    const emailInput = this.page.locator(this.emailInput);
    const validationMessage = await emailInput.evaluate((el: HTMLInputElement) => el.validationMessage);
    return validationMessage;
  }

  /**
   * Get validation error for password
   */
  async getPasswordValidationError(): Promise<string> {
    const passwordInput = this.page.locator(this.passwordInput);
    const validationMessage = await passwordInput.evaluate((el: HTMLInputElement) => el.validationMessage);
    return validationMessage;
  }
}
