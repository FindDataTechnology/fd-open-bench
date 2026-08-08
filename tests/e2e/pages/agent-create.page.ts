import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Agent create form page object
 */
export class AgentCreatePage extends BasePage {
  // Selectors
  private readonly createAgentModal = '[data-testid="create-agent-modal"]';
  private readonly agentNameInput = '[data-testid="agent-name-input"]';
  private readonly agentDescriptionInput = '[data-testid="agent-description-input"]';
  private readonly adapterTypeSelect = '[data-testid="adapter-type-select"]';
  private readonly cancelButton = '[data-testid="cancel-button"]';
  private readonly createAgentSubmitButton = '[data-testid="create-agent-submit-button"]';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Wait for create agent modal to be visible
   */
  async waitForModal(): Promise<void> {
    await this.waitForElement(this.createAgentModal);
  }

  /**
   * Enter agent name
   */
  async enterName(name: string): Promise<void> {
    await this.fillInput(this.agentNameInput, name);
  }

  /**
   * Enter agent description
   */
  async enterDescription(description: string): Promise<void> {
    await this.fillInput(this.agentDescriptionInput, description);
  }

  /**
   * Select adapter type
   */
  async selectAdapterType(adapterType: string): Promise<void> {
    await this.selectOption(this.adapterTypeSelect, adapterType);
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
    await this.clickElement(this.createAgentSubmitButton);
  }

  /**
   * Create a new agent
   */
  async createAgent(name: string, description: string, adapterType: string = 'openai'): Promise<void> {
    await this.waitForModal();
    await this.enterName(name);
    await this.enterDescription(description);
    await this.selectAdapterType(adapterType);
    await this.clickSubmit();
  }

  /**
   * Get agent name input value
   */
  async getNameValue(): Promise<string> {
    return await this.getInputValue(this.agentNameInput);
  }

  /**
   * Get agent description input value
   */
  async getDescriptionValue(): Promise<string> {
    return await this.getInputValue(this.agentDescriptionInput);
  }

  /**
   * Get selected adapter type
   */
  async getSelectedAdapterType(): Promise<string> {
    return await this.page.locator(this.adapterTypeSelect).inputValue();
  }

  /**
   * Check if modal is visible
   */
  async isModalVisible(): Promise<boolean> {
    return await this.isElementVisible(this.createAgentModal);
  }

  /**
   * Check if submit button is disabled
   */
  async isSubmitButtonDisabled(): Promise<boolean> {
    const button = this.page.locator(this.createAgentSubmitButton);
    return await button.isDisabled();
  }
}
