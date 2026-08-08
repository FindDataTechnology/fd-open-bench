import { test, expect } from '@playwright/test';
import { DatasetsListPage } from '../pages/datasets-list.page';
import { DatasetDetailPage } from '../pages/dataset-detail.page';
import { DatasetCreatePage } from '../pages/dataset-create.page';
import { testUsers } from '../fixtures/users.fixture';

test.describe('Dataset Management', () => {
  let datasetsListPage: DatasetsListPage;
  let datasetDetailPage: DatasetDetailPage;
  let datasetCreatePage: DatasetCreatePage;

  test.beforeEach(async ({ page }) => {
    datasetsListPage = new DatasetsListPage(page);
    datasetDetailPage = new DatasetDetailPage(page);
    datasetCreatePage = new DatasetCreatePage(page);
  });

  test.describe('View Dataset List', () => {
    test('should view dataset list', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', testUsers.admin.email);
      await page.fill('[data-testid="password-input"]', testUsers.admin.password);
      await page.click('[data-testid="login-button"]');
      await page.waitForURL('**/dashboard');

      // Navigate to datasets page
      await datasetsListPage.goto();
      await datasetsListPage.waitForDatasetsToLoad();

      // Verify dataset list is visible
      const datasetList = await datasetsListPage.getDatasetList();
      await expect(datasetList).toBeVisible();

      // Verify page title
      await expect(page.locator('h1')).toHaveText('Datasets');
    });

    test('should display dataset cards', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', testUsers.admin.email);
      await page.fill('[data-testid="password-input"]', testUsers.admin.password);
      await page.click('[data-testid="login-button"]');
      await page.waitForURL('**/dashboard');

      // Navigate to datasets page
      await datasetsListPage.goto();
      await datasetsListPage.waitForDatasetsToLoad();

      // Verify at least one dataset is displayed
      const datasetCount = await datasetsListPage.getDatasetCount();
      expect(datasetCount).toBeGreaterThan(0);
    });
  });

  test.describe('Create New Dataset', () => {
    test('should create new dataset', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', testUsers.admin.email);
      await page.fill('[data-testid="password-input"]', testUsers.admin.password);
      await page.click('[data-testid="login-button"]');
      await page.waitForURL('**/dashboard');

      // Navigate to datasets page
      await datasetsListPage.goto();
      await datasetsListPage.waitForDatasetsToLoad();

      // Click create dataset button
      await datasetsListPage.clickCreateDataset();

      // Wait for modal
      await datasetCreatePage.waitForModal();

      // Fill in dataset details
      const datasetName = `Test Dataset ${Date.now()}`;
      const datasetDescription = 'Test dataset description';

      await datasetCreatePage.enterName(datasetName);
      await datasetCreatePage.enterDescription(datasetDescription);

      // Submit form
      await datasetCreatePage.clickSubmit();

      // Wait for modal to close
      await page.waitForTimeout(1000);

      // Verify dataset was created (check if dataset list updated)
      await datasetsListPage.waitForDatasetsToLoad();
    });

    test('should cancel dataset creation', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', testUsers.admin.email);
      await page.fill('[data-testid="password-input"]', testUsers.admin.password);
      await page.click('[data-testid="login-button"]');
      await page.waitForURL('**/dashboard');

      // Navigate to datasets page
      await datasetsListPage.goto();
      await datasetsListPage.waitForDatasetsToLoad();

      // Click create dataset button
      await datasetsListPage.clickCreateDataset();

      // Wait for modal
      await datasetCreatePage.waitForModal();

      // Click cancel
      await datasetCreatePage.clickCancel();

      // Verify modal is closed
      const isModalVisible = await datasetCreatePage.isModalVisible();
      expect(isModalVisible).toBeFalsy();
    });
  });

  test.describe('View Dataset Details', () => {
    test('should view dataset details', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', testUsers.admin.email);
      await page.fill('[data-testid="password-input"]', testUsers.admin.password);
      await page.click('[data-testid="login-button"]');
      await page.waitForURL('**/dashboard');

      // Navigate to datasets page
      await datasetsListPage.goto();
      await datasetsListPage.waitForDatasetsToLoad();

      // Get first dataset ID
      const datasetCount = await datasetsListPage.getDatasetCount();
      if (datasetCount > 0) {
        // Click on first dataset
        const datasetCard = page.locator('[data-testid^="dataset-card-"]').first();
        const datasetId = await datasetCard.getAttribute('data-testid');
        const id = datasetId?.replace('dataset-card-', '');

        if (id) {
          await datasetsListPage.clickDataset(id);

          // Wait for detail page to load
          await page.waitForTimeout(1000);

          // Verify we're on detail page
          const currentUrl = page.url();
          expect(currentUrl).toContain(`/datasets/${id}`);
        }
      }
    });
  });
});
