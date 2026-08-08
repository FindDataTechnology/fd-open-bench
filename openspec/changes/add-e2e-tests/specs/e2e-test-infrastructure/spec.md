## ADDED Requirements

### Requirement: Playwright test framework installation
The system SHALL install Playwright as a development dependency with support for Chromium, Firefox, and WebKit browsers.

#### Scenario: Install Playwright and browsers
- **WHEN** developer runs `npm install -D @playwright/test`
- **THEN** Playwright is installed in node_modules
- **AND** browsers can be installed via `npx playwright install`

### Requirement: Playwright configuration file
The system SHALL provide a playwright.config.ts file with configuration for test execution, including base URL, test directory, timeout settings, and reporter configuration.

#### Scenario: Configuration file exists
- **WHEN** project is initialized
- **THEN** playwright.config.ts exists in project root
- **AND** configuration includes baseURL pointing to http://localhost:3001
- **AND** configuration includes testDir pointing to tests/e2e
- **AND** configuration includes timeout of 30000ms per test
- **AND** configuration includes reporters for HTML and JSON output

### Requirement: Test directory structure
The system SHALL organize e2e tests in a structured directory with separate folders for pages, fixtures, utils, and specs.

#### Scenario: Directory structure created
- **WHEN** e2e test infrastructure is set up
- **THEN** tests/e2e/pages/ directory exists
- **AND** tests/e2e/fixtures/ directory exists
- **AND** tests/e2e/utils/ directory exists
- **AND** tests/e2e/specs/ directory exists

### Requirement: Page Object Model base class
The system SHALL provide a base page object class with common methods for navigation, waiting, and element interaction.

#### Scenario: Base page object exists
- **WHEN** page objects are implemented
- **THEN** tests/e2e/pages/base.page.ts exists
- **AND** base class includes navigateTo() method
- **AND** base class includes waitForElement() method
- **AND** base class includes clickElement() method

### Requirement: Test data fixtures
The system SHALL provide test data fixtures for users, agents, datasets, and evaluations with factory functions for creating test entities.

#### Scenario: User fixtures exist
- **WHEN** test fixtures are created
- **THEN** tests/e2e/fixtures/users.fixture.ts exists
- **AND** fixture includes admin user with email admin@example.com
- **AND** fixture includes regular user with email user@example.com
- **AND** fixture includes factory function createUser()

### Requirement: Database seeding utilities
The system SHALL provide utilities for seeding test data into the database and cleaning up after tests.

#### Scenario: Database utilities exist
- **WHEN** database utilities are created
- **THEN** tests/e2e/utils/db.utils.ts exists
- **AND** utility includes seedTestData() function
- **AND** utility includes cleanupTestData() function
- **AND** utility uses direct database operations for speed

### Requirement: Authentication utilities
The system SHALL provide utilities for authenticating tests via API to bypass login UI for non-auth tests.

#### Scenario: Auth utilities exist
- **WHEN** auth utilities are created
- **THEN** tests/e2e/utils/auth.utils.ts exists
- **AND** utility includes loginViaApi() function
- **AND** utility returns session cookie for authenticated requests
- **AND** utility can be used in test setup

### Requirement: CI/CD pipeline integration
The system SHALL configure GitHub Actions workflow to run e2e tests on every pull request.

#### Scenario: GitHub Actions workflow exists
- **WHEN** CI/CD is configured
- **THEN** .github/workflows/e2e-tests.yml exists
- **AND** workflow runs on pull_request events
- **AND** workflow installs dependencies
- **AND** workflow starts backend and frontend servers
- **AND** workflow runs Playwright tests
- **AND** workflow uploads test results as artifacts

### Requirement: Test result artifacts
The system SHALL store test results, screenshots, and videos as GitHub Actions artifacts for debugging.

#### Scenario: Artifacts are uploaded
- **WHEN** e2e tests run in CI/CD
- **THEN** test results are saved in playwright-report/ directory
- **AND** screenshots are saved on test failure
- **AND** videos are recorded for all tests
- **AND** artifacts are uploaded to GitHub Actions

### Requirement: Parallel test execution
The system SHALL support parallel test execution with configurable number of workers.

#### Scenario: Parallel execution configured
- **WHEN** playwright.config.ts is configured
- **AND** fullyParallel is set to true
- **AND** workers is set to 4 (or CPU count)
- **THEN** tests run in parallel across 4 workers
- **AND** total execution time is reduced by ~75%

### Requirement: Test retry configuration
The system SHALL configure automatic retry for flaky tests with maximum 2 retries.

#### Scenario: Retry configured
- **WHEN** playwright.config.ts is configured
- **AND** retries is set to 2
- **THEN** failed tests are automatically retried up to 2 times
- **AND** test passes if any retry succeeds

### Requirement: Test timeout configuration
The system SHALL configure test timeout of 30 seconds per test.

#### Scenario: Timeout configured
- **WHEN** playwright.config.ts is configured
- **AND** timeout is set to 30000
- **THEN** tests fail if they take longer than 30 seconds
- **AND** timeout prevents hanging tests
