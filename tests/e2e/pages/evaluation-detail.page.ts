import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Evaluation detail page object
 */
export class EvaluationDetailPage extends BasePage {
  // Selectors
  private readonly evaluationStatus = '[data-testid="evaluation-status"]';
  private readonly resultsList = 'table';
  private readonly viewTraceButton = 'button:has-text("View Trace")';
  private readonly cancelButton = 'button:has-text("Cancel")';
  private readonly retryButton = 'button:has-text("Retry")';
  private readonly exportButton = 'button:has-text("Export")';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to evaluation detail page
   */
  async goto(evaluationId: string): Promise<void> {
    await this.navigateTo(`/evaluations/${evaluationId}`);
  }

  /**
   * Get evaluation status
   */
  async getEvaluationStatus(): Promise<string> {
    return await this.getTextContent(this.evaluationStatus);
  }

  /**
   * Get results list
   */
  async getResultsList(): Promise<Locator> {
    return this.page.locator(this.resultsList);
  }

  /**
   * Get result count
   */
  async getResultCount(): Promise<number> {
    const rows = this.page.locator('tbody tr');
    return await rows.count();
  }

  /**
   * Click view trace button
   */
  async clickViewTrace(): Promise<void> {
    await this.clickElement(this.viewTraceButton);
  }

  /**
   * Click cancel button
   */
  async clickCancel(): Promise<void> {
    await this.clickElement(this.cancelButton);
  }

  /**
   * Click retry button
   */
  async clickRetry(): Promise<void> {
    await this.clickElement(this.retryButton);
  }

  /**
   * Click export button
   */
  async clickExport(): Promise<void> {
    await this.clickElement(this.exportButton);
  }

  /**
   * Check if view trace button is visible
   */
  async isViewTraceButtonVisible(): Promise<boolean> {
    return await this.isElementVisible(this.viewTraceButton);
  }

  /**
   * Check if cancel button is visible
   */
  async isCancelButtonVisible(): Promise<boolean> {
    return await this.isElementVisible(this.cancelButton);
  }

  /**
   * Check if retry button is visible
   */
  async isRetryButtonVisible(): Promise<boolean> {
    return await this.isElementVisible(this.retryButton);
  }

  /**
   * Check if export button is visible
   */
  async isExportButtonVisible(): Promise<boolean> {
    return await this.isElementVisible(this.exportButton);
  }
}
