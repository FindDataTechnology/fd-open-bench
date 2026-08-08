import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Page object for the Create Evaluation Modal
 */
export class EvaluationCreatePage extends BasePage {
  private readonly modal: Locator;
  private readonly agentSelector: Locator;
  private readonly datasetSelector: Locator;
  private readonly cancelButton: Locator;
  private readonly submitButton: Locator;

  constructor(page: Page) {
    super(page);
    this.modal = page.locator('[data-testid="create-evaluation-modal"]');
    this.agentSelector = page.locator('[data-testid="agent-selector"]');
    this.datasetSelector = page.locator('[data-testid="dataset-selector"]');
    this.cancelButton = page.locator('[data-testid="cancel-button"]');
    this.submitButton = page.locator('[data-testid="create-evaluation-submit-button"]');
  }

  /**
   * Wait for the modal to be visible
   */
  async waitForModal(): Promise<void> {
    await this.modal.waitFor({ state: 'visible' });
  }

  /**
   * Select an agent from the dropdown
   */
  async selectAgent(agentName: string): Promise<void> {
    await this.agentSelector.selectOption({ label: agentName });
  }

  /**
   * Select a dataset from the dropdown
   */
  async selectDataset(datasetName: string): Promise<void> {
    await this.datasetSelector.selectOption({ label: datasetName });
  }

  /**
   * Click the cancel button
   */
  async clickCancel(): Promise<void> {
    await this.cancelButton.click();
  }

  /**
   * Click the submit button
   */
  async clickSubmit(): Promise<void> {
    await this.submitButton.click();
  }

  /**
   * Check if the modal is visible
   */
  async isModalVisible(): Promise<boolean> {
    return await this.modal.isVisible();
  }

  /**
   * Get the currently selected agent
   */
  async getSelectedAgent(): Promise<string> {
    return await this.agentSelector.inputValue();
  }

  /**
   * Get the currently selected dataset
   */
  async getSelectedDataset(): Promise<string> {
    return await this.datasetSelector.inputValue();
  }

  /**
   * Check if submit button is disabled
   */
  async isSubmitButtonDisabled(): Promise<boolean> {
    return await this.submitButton.isDisabled();
  }
}
