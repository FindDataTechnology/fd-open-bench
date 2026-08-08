import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Dataset detail page object
 */
export class DatasetDetailPage extends BasePage {
  // Selectors
  private readonly datasetName = 'h1';
  private readonly datasetDescription = 'p';
  private readonly goldenList = 'table';
  private readonly importGoldensButton = 'button:has-text("Import Goldens")';
  private readonly editButton = 'button:has-text("Edit")';
  private readonly deleteButton = 'button:has-text("Delete")';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to dataset detail page
   */
  async goto(datasetId: string): Promise<void> {
    await this.navigateTo(`/datasets/${datasetId}`);
  }

  /**
   * Get dataset name
   */
  async getDatasetName(): Promise<string> {
    return await this.getTextContent(this.datasetName);
  }

  /**
   * Get dataset description
   */
  async getDatasetDescription(): Promise<string> {
    const descriptionElement = this.page.locator(this.datasetDescription).first();
    return await descriptionElement.textContent() || '';
  }

  /**
   * Get golden list
   */
  async getGoldenList(): Promise<Locator> {
    return this.page.locator(this.goldenList);
  }

  /**
   * Get golden count
   */
  async getGoldenCount(): Promise<number> {
    const rows = this.page.locator('tbody tr');
    return await rows.count();
  }

  /**
   * Click import goldens button
   */
  async clickImportGoldens(): Promise<void> {
    await this.clickElement(this.importGoldensButton);
  }

  /**
   * Click edit button
   */
  async clickEdit(): Promise<void> {
    await this.clickElement(this.editButton);
  }

  /**
   * Click delete button
   */
  async clickDelete(): Promise<void> {
    await this.clickElement(this.deleteButton);
  }

  /**
   * Check if import button is visible
   */
  async isImportButtonVisible(): Promise<boolean> {
    return await this.isElementVisible(this.importGoldensButton);
  }

  /**
   * Check if edit button is visible
   */
  async isEditButtonVisible(): Promise<boolean> {
    return await this.isElementVisible(this.editButton);
  }

  /**
   * Check if delete button is visible
   */
  async isDeleteButtonVisible(): Promise<boolean> {
    return await this.isElementVisible(this.deleteButton);
  }
}
