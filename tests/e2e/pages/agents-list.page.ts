import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Agents list page object
 */
export class AgentsListPage extends BasePage {
  // Selectors
  private readonly createAgentButton = '[data-testid="create-agent-button"]';
  private readonly agentList = '[data-testid="agent-list"]';
  private readonly loadingIndicator = 'text=Loading agents...';

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to agents page
   */
  async goto(): Promise<void> {
    await this.navigateTo('/agents');
  }

  /**
   * Wait for agents list to load
   */
  async waitForAgentsToLoad(): Promise<void> {
    await this.waitForElementHidden(this.loadingIndicator);
    await this.waitForElement(this.agentList);
  }

  /**
   * Click create agent button
   */
  async clickCreateAgent(): Promise<void> {
    await this.clickElement(this.createAgentButton);
  }

  /**
   * Get agent list
   */
  async getAgentList(): Promise<Locator> {
    return this.page.locator(this.agentList);
  }

  /**
   * Get agent count
   */
  async getAgentCount(): Promise<number> {
    const agents = this.page.locator('[data-testid^="agent-card-"]');
    return await agents.count();
  }

  /**
   * Click on an agent card
   */
  async clickAgent(agentId: string): Promise<void> {
    await this.clickElement(`[data-testid="agent-card-${agentId}"]`);
  }

  /**
   * Check if agent exists
   */
  async isAgentVisible(agentId: string): Promise<boolean> {
    return await this.isElementVisible(`[data-testid="agent-card-${agentId}"]`);
  }

  /**
   * Get agent name
   */
  async getAgentName(agentId: string): Promise<string> {
    const agentCard = this.page.locator(`[data-testid="agent-card-${agentId}"]`);
    const nameElement = agentCard.locator('h3');
    return await nameElement.textContent() || '';
  }

  /**
   * Get agent adapter type
   */
  async getAgentAdapterType(agentId: string): Promise<string> {
    const agentCard = this.page.locator(`[data-testid="agent-card-${agentId}"]`);
    const adapterElement = agentCard.locator('p').first();
    return await adapterElement.textContent() || '';
  }
}
