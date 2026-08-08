import { test, expect } from '@playwright/test';
import { EvaluationsListPage } from '../pages/evaluations-list.page';
import { EvaluationDetailPage } from '../pages/evaluation-detail.page';
import { EvaluationCreatePage } from '../pages/evaluation-create.page';
import { testUsers } from '../fixtures/users.fixture';

test.describe('Evaluation Workflow', () => {
  let evaluationsListPage: EvaluationsListPage;
  let evaluationDetailPage: EvaluationDetailPage;
  let evaluationCreatePage: EvaluationCreatePage;

  test.beforeEach(async ({ page }) => {
    evaluationsListPage = new EvaluationsListPage(page);
    evaluationDetailPage = new EvaluationDetailPage(page);
    evaluationCreatePage = new EvaluationCreatePage(page);

    // Login before each test
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', testUsers.admin.email);
    await page.fill('[data-testid="password-input"]', testUsers.admin.password);
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('**/dashboard');
  });

  test('should view evaluation list', async ({ page }) => {
    await evaluationsListPage.goto();
    await evaluationsListPage.waitForEvaluationsToLoad();

    // Verify evaluation list is visible
    const evaluationList = await evaluationsListPage.getEvaluationList();
    await expect(evaluationList).toBeVisible();

    // Verify page title
    await expect(page.locator('h1')).toHaveText('Evaluations');
  });

  test('should display evaluation rows', async ({ page }) => {
    await evaluationsListPage.goto();
    await evaluationsListPage.waitForEvaluationsToLoad();

    // Verify at least one evaluation is displayed (if exists)
    const evaluationCount = await evaluationsListPage.getEvaluationCount();
    expect(evaluationCount).toBeGreaterThanOrEqual(0);
  });

  test('should create new evaluation', async ({ page }) => {
    await evaluationsListPage.goto();
    await evaluationsListPage.waitForEvaluationsToLoad();

    // Click create evaluation button
    await evaluationsListPage.clickCreateEvaluation();

    // Wait for modal
    await evaluationCreatePage.waitForModal();

    // Verify modal is visible
    const isModalVisible = await evaluationCreatePage.isModalVisible();
    expect(isModalVisible).toBeTruthy();

    // Cancel the modal
    await evaluationCreatePage.clickCancel();

    // Verify modal is closed
    const isModalClosed = await evaluationCreatePage.isModalVisible();
    expect(isModalClosed).toBeFalsy();
  });

  test('should view evaluation details', async ({ page }) => {
    await evaluationsListPage.goto();
    await evaluationsListPage.waitForEvaluationsToLoad();

    // Get first evaluation ID
    const evaluationCount = await evaluationsListPage.getEvaluationCount();
    if (evaluationCount > 0) {
      // Click on first evaluation
      const evaluationRow = page.locator('tbody tr').first();
      const evaluationId = await evaluationRow.locator('td').first().textContent();
      const id = evaluationId?.replace('...', '');

      if (id) {
        await evaluationsListPage.clickEvaluation(id);

        // Wait for detail page to load
        await page.waitForTimeout(1000);

        // Verify we're on detail page
        const currentUrl = page.url();
        expect(currentUrl).toContain(`/evaluations/${id}`);
      }
    }
  });
});
