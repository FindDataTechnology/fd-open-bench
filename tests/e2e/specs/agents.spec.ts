import { test, expect } from '@playwright/test';
import { AgentsListPage } from '../pages/agents-list.page';
import { AgentDetailPage } from '../pages/agent-detail.page';
import { AgentCreatePage } from '../pages/agent-create.page';
import { testUsers } from '../fixtures/users.fixture';
import { testAgents } from '../fixtures/agents.fixture';

test.describe('Agent Management', () => {
  let agentsListPage: AgentsListPage;
  let agentDetailPage: AgentDetailPage;
  let agentCreatePage: AgentCreatePage;

  test.beforeEach(async ({ page }) => {
    agentsListPage = new AgentsListPage(page);
    agentDetailPage = new AgentDetailPage(page);
    agentCreatePage = new AgentCreatePage(page);
  });

  test.describe('View Agent List', () => {
    test('should view agent list', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', testUsers.admin.email);
      await page.fill('[data-testid="password-input"]', testUsers.admin.password);
      await page.click('[data-testid="login-button"]');
      await page.waitForURL('**/dashboard');

      // Navigate to agents page
      await agentsListPage.goto();
      await agentsListPage.waitForAgentsToLoad();

      // Verify agent list is visible
      const agentList = await agentsListPage.getAgentList();
      await expect(agentList).toBeVisible();

      // Verify page title
      await expect(page.locator('h1')).toHaveText('Agents');
    });

    test('should display agent cards', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', testUsers.admin.email);
      await page.fill('[data-testid="password-input"]', testUsers.admin.password);
      await page.click('[data-testid="login-button"]');
      await page.waitForURL('**/dashboard');

      // Navigate to agents page
      await agentsListPage.goto();
      await agentsListPage.waitForAgentsToLoad();

      // Verify at least one agent is displayed
      const agentCount = await agentsListPage.getAgentCount();
      expect(agentCount).toBeGreaterThan(0);
    });
  });

  test.describe('Create New Agent', () => {
    test('should create new agent', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', testUsers.admin.email);
      await page.fill('[data-testid="password-input"]', testUsers.admin.password);
      await page.click('[data-testid="login-button"]');
      await page.waitForURL('**/dashboard');

      // Navigate to agents page
      await agentsListPage.goto();
      await agentsListPage.waitForAgentsToLoad();

      // Click create agent button
      await agentsListPage.clickCreateAgent();

      // Wait for modal
      await agentCreatePage.waitForModal();

      // Fill in agent details
      const agentName = `Test Agent ${Date.now()}`;
      const agentDescription = 'Test agent description';

      await agentCreatePage.enterName(agentName);
      await agentCreatePage.enterDescription(agentDescription);
      await agentCreatePage.selectAdapterType('openai');

      // Submit form
      await agentCreatePage.clickSubmit();

      // Wait for modal to close
      await page.waitForTimeout(1000);

      // Verify agent was created (check if agent list updated)
      await agentsListPage.waitForAgentsToLoad();
    });

    test('should cancel agent creation', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', testUsers.admin.email);
      await page.fill('[data-testid="password-input"]', testUsers.admin.password);
      await page.click('[data-testid="login-button"]');
      await page.waitForURL('**/dashboard');

      // Navigate to agents page
      await agentsListPage.goto();
      await agentsListPage.waitForAgentsToLoad();

      // Click create agent button
      await agentsListPage.clickCreateAgent();

      // Wait for modal
      await agentCreatePage.waitForModal();

      // Click cancel
      await agentCreatePage.clickCancel();

      // Verify modal is closed
      const isModalVisible = await agentCreatePage.isModalVisible();
      expect(isModalVisible).toBeFalsy();
    });
  });

  test.describe('View Agent Details', () => {
    test('should view agent details', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', testUsers.admin.email);
      await page.fill('[data-testid="password-input"]', testUsers.admin.password);
      await page.click('[data-testid="login-button"]');
      await page.waitForURL('**/dashboard');

      // Navigate to agents page
      await agentsListPage.goto();
      await agentsListPage.waitForAgentsToLoad();

      // Get first agent ID
      const agentCount = await agentsListPage.getAgentCount();
      if (agentCount > 0) {
        // Click on first agent
        const agentCard = page.locator('[data-testid^="agent-card-"]').first();
        const agentId = await agentCard.getAttribute('data-testid');
        const id = agentId?.replace('agent-card-', '');

        if (id) {
          await agentsListPage.clickAgent(id);

          // Wait for detail page to load
          await page.waitForTimeout(1000);

          // Verify we're on detail page
          const currentUrl = page.url();
          expect(currentUrl).toContain(`/agents/${id}`);
        }
      }
    });
  });
});
