import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Evaluations list page object
 */
export class EvaluationsListPage extends BasePage {
  // Selectors
  private readonly createEvaluationButton = '[data-testid="create-evaluation-button"]';
  private readonly evaluationList = '[data-testid="evaluation-list"]';
  private readonly loadingIndicator = 'text=Loading evaluations...';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to evaluations page
   */
  async goto(): Promise<void> {
    await this.navigateTo('/evaluations');
  }

  /**
   * Wait for evaluations list to load
   */
  async waitForEvaluationsToLoad(): Promise<void> {
    await this.waitForElementHidden(this.loadingIndicator);
    await this.waitForElement(this.evaluationList);
  }

  /**
   * Click create evaluation button
   */
  async clickCreateEvaluation(): Promise<void> {
    await this.clickElement(this.createEvaluationButton);
  }

  /**
   * Get evaluation list
   */
  async getEvaluationList(): Promise<Locator> {
    return this.page.locator(this.evaluationList);
  }

  /**
   * Get evaluation count
   */
  async getEvaluationCount(): Promise<number> {
    const rows = this.page.locator('tbody tr');
    return await rows.count();
  }

  /**
   * Click on an evaluation row
   */
  async clickEvaluation(evaluationId: string): Promise<void> {
    await this.clickElement(`tr:has-text("${evaluationId}")`);
  }

  /**
   * Check if evaluation exists
   */
  async isEvaluationVisible(evaluationId: string): Promise<boolean> {
    return await this.isElementVisible(`tr:has-text("${evaluationId}")`);
  }

  /**
   * Get evaluation status
   */
  async getEvaluationStatus(evaluationId: string): Promise<string> {
    const row = this.page.locator(`tr:has-text("${evaluationId}")`);
    const statusElement = row.locator('td').nth(3);
    return await statusElement.textContent() || '';
  }

  /**
   * Get evaluation progress
   */
  async getEvaluationProgress(evaluationId: string): Promise<string> {
    const row = this.page.locator(`tr:has-text("${evaluationId}")`);
    const progressElement = row.locator('td').nth(4);
    return await progressElement.textContent() || '';
  }
}
