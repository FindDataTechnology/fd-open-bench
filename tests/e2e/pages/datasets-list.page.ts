import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Datasets list page object
 */
export class DatasetsListPage extends BasePage {
  // Selectors
  private readonly createDatasetButton = '[data-testid="create-dataset-button"]';
  private readonly datasetList = '[data-testid="dataset-list"]';
  private readonly loadingIndicator = 'text=Loading datasets...';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to datasets page
   */
  async goto(): Promise<void> {
    await this.navigateTo('/datasets');
  }

  /**
   * Wait for datasets list to load
   */
  async waitForDatasetsToLoad(): Promise<void> {
    await this.waitForElementHidden(this.loadingIndicator);
    await this.waitForElement(this.datasetList);
  }

  /**
   * Click create dataset button
   */
  async clickCreateDataset(): Promise<void> {
    await this.clickElement(this.createDatasetButton);
  }

  /**
   * Get dataset list
   */
  async getDatasetList(): Promise<Locator> {
    return this.page.locator(this.datasetList);
  }

  /**
   * Get dataset count
   */
  async getDatasetCount(): Promise<number> {
    const datasets = this.page.locator('[data-testid^="dataset-card-"]');
    return await datasets.count();
  }

  /**
   * Click on a dataset card
   */
  async clickDataset(datasetId: string): Promise<void> {
    await this.clickElement(`[data-testid="dataset-card-${datasetId}"]`);
  }

  /**
   * Check if dataset exists
   */
  async isDatasetVisible(datasetId: string): Promise<boolean> {
    return await this.isElementVisible(`[data-testid="dataset-card-${datasetId}"]`);
  }

  /**
   * Get dataset name
   */
  async getDatasetName(datasetId: string): Promise<string> {
    const datasetCard = this.page.locator(`[data-testid="dataset-card-${datasetId}"]`);
    const nameElement = datasetCard.locator('h3');
    return await nameElement.textContent() || '';
  }

  /**
   * Get dataset golden count
   */
  async getDatasetGoldenCount(datasetId: string): Promise<string> {
    const datasetCard = this.page.locator(`[data-testid="dataset-card-${datasetId}"]`);
    const countElement = datasetCard.locator('p').first();
    return await countElement.textContent() || '';
  }
}
