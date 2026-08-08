# End-to-End Tests

This directory contains end-to-end (e2e) tests for the FD Open Bench platform using Playwright.

## Overview

The e2e tests verify complete user workflows from start to finish, ensuring that all critical user journeys work correctly in a real browser environment.

## Test Structure

```
tests/e2e/
├── pages/              # Page objects for each page
│   ├── base.page.ts    # Base page object with common methods
│   ├── login.page.ts   # Login page object
│   └── ...
├── fixtures/           # Test data and fixtures
│   ├── users.fixture.ts
│   ├── agents.fixture.ts
│   ├── datasets.fixture.ts
│   └── evaluations.fixture.ts
├── utils/              # Test utilities
│   ├── auth.utils.ts   # Authentication utilities
│   └── db.utils.ts     # Database utilities
├── specs/              # Test specifications
│   ├── auth.spec.ts    # Authentication tests
│   └── ...
└── playwright.config.ts # Playwright configuration
```

## Prerequisites

1. Node.js 18+ installed
2. Backend server running on `http://localhost:8001`
3. Frontend server running on `http://localhost:3001`
4. Database initialized with test data

## Running Tests

### Run all tests

```bash
npm run test:e2e
```

### Run tests in headed mode (visible browser)

```bash
npm run test:e2e:headed
```

### Run specific test file

```bash
npx playwright test tests/e2e/specs/auth.spec.ts
```

### Run tests with specific browser

```bash
npx playwright test --project=chromium
```

### Run tests in debug mode

```bash
npx playwright test --debug
```

### Run tests with UI mode

```bash
npx playwright test --ui
```

## Test Reports

After running tests, view the HTML report:

```bash
npx playwright show-report
```

## Test Data Management

### Seeding test data

Before running tests, seed the database with test data:

```bash
python scripts/seed_test_data.py
```

### Cleaning up test data

After running tests, clean up test data:

```bash
python scripts/cleanup_test_data.py
```

## Writing New Tests

### 1. Create a page object

Create a new page object in `tests/e2e/pages/`:

```typescript
import { Page } from '@playwright/test';
import { BasePage } from './base.page';

export class MyPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // Add page-specific methods
  async doSomething(): Promise<void> {
    await this.clickElement('[data-testid="my-button"]');
  }
}
```

### 2. Create a test spec

Create a new test spec in `tests/e2e/specs/`:

```typescript
import { test, expect } from '@playwright/test';
import { MyPage } from '../pages/my.page';

test.describe('My Feature', () => {
  let myPage: MyPage;

  test.beforeEach(async ({ page }) => {
    myPage = new MyPage(page);
    await myPage.goto();
  });

  test('should do something', async () => {
    await myPage.doSomething();
    // Add assertions
  });
});
```

### 3. Add data-testid attributes

Add `data-testid` attributes to frontend components for reliable element selection:

```tsx
<button data-testid="my-button">Click me</button>
```

## Configuration

The Playwright configuration is in `playwright.config.ts` at the project root.

Key settings:
- **Base URL**: `http://localhost:3001`
- **Timeout**: 30 seconds per test
- **Retries**: 2 retries on CI, 0 locally
- **Workers**: 1 worker on CI, auto locally
- **Reporters**: HTML, JSON, and list reporters

## CI/CD Integration

Tests are automatically run on every pull request via GitHub Actions.

The workflow:
1. Starts backend and frontend servers
2. Seeds test data
3. Runs Playwright tests
4. Uploads test results as artifacts

## Troubleshooting

### Tests fail with "Timeout exceeded"

- Increase timeout in `playwright.config.ts`
- Check if servers are running
- Check network connectivity

### Tests fail with "Element not found"

- Verify `data-testid` attributes are present
- Check if page has fully loaded
- Use `waitForElement()` before interacting

### Tests fail with "Authentication failed"

- Verify backend is running on port 8001
- Check test user credentials in fixtures
- Verify database is seeded with test data

### Tests are flaky

- Add explicit waits using `waitForElement()`
- Avoid hardcoded timeouts
- Use `waitForNavigation()` after navigation actions
- Consider using `waitForLoadState('networkidle')`

## Best Practices

1. **Use Page Object Model**: Encapsulate page interactions in page objects
2. **Use data-testid**: Prefer `data-testid` over CSS selectors or text
3. **Wait explicitly**: Don't rely on implicit waits
4. **Keep tests independent**: Each test should be able to run in isolation
5. **Use fixtures**: Reuse test data through fixtures
6. **Assert meaningfully**: Assert on what matters to the user
7. **Keep tests fast**: Avoid unnecessary waits or actions

## Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Testing Library](https://testing-library.com/docs/)

## Support

For questions or issues, contact the development team or create an issue in the repository.
