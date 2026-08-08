import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Dataset create form page object
 */
export class DatasetCreatePage extends BasePage {
  // Selectors
  private readonly createDatasetModal = '[data-testid="create-dataset-modal"]';
  private readonly datasetNameInput = '[data-testid="dataset-name-input"]';
  private readonly datasetDescriptionInput = '[data-testid="dataset-description-input"]';
  private readonly cancelButton = '[data-testid="cancel-button"]';
  private readonly createDatasetSubmitButton = '[data-testid="create-dataset-submit-button"]';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Wait for create dataset modal to be visible
   */
  async waitForModal(): Promise<void> {
    await this.waitForElement(this.createDatasetModal);
  }

  /**
   * Enter dataset name
   */
  async enterName(name: string): Promise<void> {
    await this.fillInput(this.datasetNameInput, name);
  }

  /**
   * Enter dataset description
   */
  async enterDescription(description: string): Promise<void> {
    await this.fillInput(this.datasetDescriptionInput, description);
  }

  /**
   * Click cancel button
   */
  async clickCancel(): Promise<void> {
    await this.clickElement(this.cancelButton);
  }

  /**
   * Click submit button
   */
  async clickSubmit(): Promise<void> {
    await this.clickElement(this.createDatasetSubmitButton);
  }

  /**
   * Create a new dataset
   */
  async createDataset(name: string, description: string): Promise<void> {
    await this.waitForModal();
    await this.enterName(name);
    await this.enterDescription(description);
    await this.clickSubmit();
  }

  /**
   * Get dataset name input value
   */
  async getNameValue(): Promise<string> {
    return await this.getInputValue(this.datasetNameInput);
  }

  /**
   * Get dataset description input value
   */
  async getDescriptionValue(): Promise<string> {
    return await this.getInputValue(this.datasetDescriptionInput);
  }

  /**
   * Check if modal is visible
   */
  async isModalVisible(): Promise<boolean> {
    return await this.isElementVisible(this.createDatasetModal);
  }

  /**
   * Check if submit button is disabled
   */
  async isSubmitButtonDisabled(): Promise<boolean> {
    const button = this.page.locator(this.createDatasetSubmitButton);
    return await button.isDisabled();
  }
}
