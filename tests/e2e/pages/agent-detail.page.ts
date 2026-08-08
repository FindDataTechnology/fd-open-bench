import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Agent detail page object
 */
export class AgentDetailPage extends BasePage {
  // Selectors
  private readonly agentName = 'h1';
  private readonly agentDescription = 'p';
  private readonly editButton = 'button:has-text("Edit")';
  private readonly deleteButton = 'button:has-text("Delete")';
  private readonly confirmDeleteButton = 'button:has-text("Confirm")';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to agent detail page
   */
  async goto(agentId: string): Promise<void> {
    await this.navigateTo(`/agents/${agentId}`);
  }

  /**
   * Get agent name
   */
  async getAgentName(): Promise<string> {
    return await this.getTextContent(this.agentName);
  }

  /**
   * Get agent description
   */
  async getAgentDescription(): Promise<string> {
    const descriptionElement = this.page.locator(this.agentDescription).first();
    return await descriptionElement.textContent() || '';
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
   * Confirm delete
   */
  async confirmDelete(): Promise<void> {
    await this.clickElement(this.confirmDeleteButton);
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
