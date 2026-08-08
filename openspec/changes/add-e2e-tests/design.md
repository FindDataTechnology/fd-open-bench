## Context

The FD Open Bench platform is a web-based agent performance evaluation system built with FastAPI (backend) and React + TypeScript (frontend). The platform provides features for managing agents, datasets, evaluations, and analyzing costs. Currently, the project has unit tests and integration tests but lacks comprehensive end-to-end tests that verify complete user workflows in a real browser environment.

**Current State:**
- Backend: FastAPI with REST API endpoints
- Frontend: React + TypeScript with Vite
- Database: SQLite (development) / PostgreSQL (production)
- Authentication: JWT-based with bcrypt password hashing
- Existing tests: Unit tests and integration tests for backend APIs
- CI/CD: GitHub Actions configured for linting and unit tests

**Constraints:**
- Tests must run in headless mode for CI/CD
- Tests must be fast enough to run on every PR (< 10 minutes total)
- Tests must be maintainable and not brittle
- Tests must work with both SQLite and PostgreSQL
- Tests must not interfere with each other (isolation)

**Stakeholders:**
- Development team: Need confidence in code changes
- QA team: Need automated regression testing
- Product team: Need assurance that user workflows work correctly
- DevOps team: Need reliable CI/CD pipeline

## Goals / Non-Goals

**Goals:**
- Implement comprehensive e2e test coverage for all critical user workflows
- Achieve >80% test coverage for user-facing features
- Set up automated test execution in CI/CD pipeline
- Provide clear test reports with screenshots and videos on failure
- Enable parallel test execution for faster feedback
- Create reusable test utilities and helpers
- Implement test data management (setup and teardown)

**Non-Goals:**
- Visual regression testing (will be added in future iteration)
- Performance testing or load testing
- Cross-browser testing (focus on Chromium initially)
- Mobile device testing
- Accessibility testing (will be added separately)
- Testing third-party integrations (mock these instead)

## Decisions

### Decision 1: Use Playwright over Cypress

**Choice:** Playwright

**Alternatives Considered:**
- **Cypress:** Popular, good DX, but limited to single tab, slower execution, no native support for multiple browsers
- **Selenium:** Mature, but verbose API, slower, requires more boilerplate
- **Puppeteer:** Good for Chrome, but limited browser support, lower-level API

**Rationale:**
- **Multi-browser support:** Playwright supports Chromium, Firefox, and WebKit out of the box
- **Parallel execution:** Built-in parallel test execution with automatic sharding
- **Auto-waiting:** Reduces flaky tests by automatically waiting for elements
- **Network interception:** Easy to mock API calls and test edge cases
- **Trace viewer:** Built-in debugging tool with timeline, screenshots, and DOM snapshots
- **Fast execution:** Faster than Cypress due to WebSocket-based communication
- **TypeScript support:** Excellent TypeScript support with type definitions
- **Active development:** Backed by Microsoft, active community, frequent updates

### Decision 2: Test Organization Structure

**Choice:** Page Object Model (POM) with test fixtures

**Structure:**
```
tests/e2e/
├── pages/              # Page objects for each page
│   ├── login.page.ts
│   ├── dashboard.page.ts
│   ├── agents.page.ts
│   └── ...
├── fixtures/           # Test data and fixtures
│   ├── users.fixture.ts
│   ├── agents.fixture.ts
│   └── ...
├── utils/              # Test utilities
│   ├── auth.utils.ts
│   ├── db.utils.ts
│   └── ...
├── specs/              # Test specifications
│   ├── auth.spec.ts
│   ├── agents.spec.ts
│   └── ...
└── playwright.config.ts
```

**Rationale:**
- **Page Object Model:** Encapsulates page interactions, reduces duplication, easier maintenance
- **Fixtures:** Reusable test data, consistent test setup
- **Utils:** Common operations (login, database operations) in one place
- **Specs:** Clear separation of test logic from page interactions

### Decision 3: Test Data Management Strategy

**Choice:** Database seeding with cleanup

**Approach:**
- Before each test suite: Seed database with test data
- After each test suite: Clean up test data
- Use transactions for test isolation where possible
- Provide factory functions for creating test entities

**Alternatives Considered:**
- **API-based setup:** Slower, depends on API stability
- **Manual setup:** Not scalable, error-prone
- **Snapshot-based:** Hard to maintain, not flexible

**Rationale:**
- **Fast:** Direct database operations are faster than API calls
- **Reliable:** No dependency on API availability
- **Flexible:** Can create any test scenario
- **Isolated:** Each test suite has clean state

### Decision 4: Authentication Testing Approach

**Choice:** Test authentication through UI, use API shortcuts for other tests

**Approach:**
- Dedicated auth test suite: Tests login, logout, session management through UI
- Other test suites: Use API to authenticate and inject session cookie
- Provide `authenticatedSetup` fixture for tests that need authentication

**Rationale:**
- **Comprehensive:** Auth flows are tested end-to-end
- **Fast:** Other tests don't need to go through login UI
- **Flexible:** Can test both authenticated and unauthenticated scenarios
- **Maintainable:** Single source of truth for authentication logic

### Decision 5: CI/CD Integration Strategy

**Choice:** GitHub Actions with artifact storage

**Approach:**
- Run e2e tests on every PR
- Store test results, screenshots, and videos as artifacts
- Run tests in parallel using multiple containers
- Cache dependencies for faster execution
- Fail PR if tests fail

**Rationale:**
- **Visibility:** Artifacts provide debugging information
- **Speed:** Parallel execution reduces feedback time
- **Reliability:** Consistent environment in CI
- **Integration:** Native GitHub integration, easy to configure

## Risks / Trade-offs

### Risk 1: Flaky Tests

**Risk:** E2E tests can be flaky due to timing issues, network latency, or environment differences.

**Mitigation:**
- Use Playwright's auto-waiting features
- Implement retry logic for flaky tests (max 2 retries)
- Use explicit waits instead of hardcoded sleeps
- Run tests in isolated containers
- Monitor flaky test rate and fix or quarantine problematic tests

### Risk 2: Slow Test Execution

**Risk:** E2E tests can be slow, blocking CI/CD pipeline.

**Mitigation:**
- Run tests in parallel (4 workers by default)
- Use API shortcuts for non-auth tests
- Optimize page loads (mock slow APIs)
- Cache test dependencies
- Set timeout limits (30s per test)

### Risk 3: Test Maintenance Burden

**Risk:** E2E tests require maintenance when UI changes.

**Mitigation:**
- Use Page Object Model to centralize UI interactions
- Use data-testid attributes instead of CSS selectors
- Keep tests focused on user workflows, not implementation details
- Regular test review and refactoring
- Clear test naming and documentation

### Risk 4: Environment Differences

**Risk:** Tests pass locally but fail in CI due to environment differences.

**Mitigation:**
- Use Docker containers for consistent environment
- Test with same database type as production
- Use environment variables for configuration
- Run tests in headless mode (same as CI)
- Document environment requirements

### Risk 5: Test Data Conflicts

**Risk:** Tests interfere with each other due to shared test data.

**Mitigation:**
- Use unique test data per test suite (UUIDs)
- Clean up test data after each suite
- Use database transactions for isolation
- Run tests in isolated containers
- Avoid shared state between tests

### Trade-off 1: Test Coverage vs. Speed

**Trade-off:** More comprehensive tests take longer to run.

**Decision:** Focus on critical user workflows first, add edge cases later. Target 80% coverage for critical paths, not 100% coverage for all features.

### Trade-off 2: Test Isolation vs. Speed

**Trade-off:** Complete isolation (fresh database per test) is slower but more reliable.

**Decision:** Use suite-level isolation (fresh database per test suite) to balance speed and reliability. Accept some risk of test interference within a suite.

### Trade-off 3: Real Browser vs. Headless

**Trade-off:** Real browser testing is more accurate but slower and harder to debug.

**Decision:** Run tests in headless mode by default for speed. Provide option to run in headed mode for debugging. Use trace viewer for detailed debugging.

## Migration Plan

**Phase 1: Infrastructure Setup (Week 1)**
- Install Playwright and dependencies
- Configure playwright.config.ts
- Set up test directory structure
- Create base page objects and utilities
- Set up CI/CD pipeline

**Phase 2: Authentication Tests (Week 2)**
- Implement login page object
- Create authentication test suite
- Test login, logout, session management
- Add test data fixtures for users
- Verify tests pass in CI/CD

**Phase 3: Core Feature Tests (Week 3-4)**
- Implement page objects for agents, datasets, evaluations
- Create test suites for each feature
- Add test data fixtures
- Implement database seeding utilities
- Verify tests pass in CI/CD

**Phase 4: Advanced Features (Week 5)**
- Implement evaluator configuration tests
- Add cost analyzer tests
- Create settings management tests
- Add visual regression tests (optional)
- Optimize test execution speed

**Phase 5: Optimization & Documentation (Week 6)**
- Optimize test execution (parallelization, caching)
- Add test documentation
- Create test maintenance guide
- Set up test coverage reporting
- Train team on writing e2e tests

**Rollback Strategy:**
- E2E tests are additive, no rollback needed
- If tests are blocking CI/CD, disable e2e job temporarily
- Fix failing tests before re-enabling

## Open Questions

**Question 1: Should we test with real LLM APIs or mock them?**

**Options:**
- A) Use real APIs (OpenAI, Anthropic) for realistic testing
- B) Mock all LLM APIs for speed and cost control
- C) Hybrid approach: Real APIs for integration tests, mocks for e2e tests

**Decision Needed:** Balance between realism and cost/speed.

**Question 2: Should we include visual regression testing?**

**Options:**
- A) Include visual regression testing from the start
- B) Add visual regression testing in future iteration
- C) Use snapshot testing for critical UI components only

**Decision Needed:** Visual regression testing adds complexity and maintenance burden.

**Question 3: How should we handle test data for production-like scenarios?**

**Options:**
- A) Use synthetic data generated by factories
- B) Use anonymized production data (with consent)
- C) Use predefined test scenarios with realistic data

**Decision Needed:** Balance between realism and data privacy/security.

**Question 4: Should we run e2e tests on every commit or only on PR?**

**Options:**
- A) Run on every commit to main branch
- B) Run on every PR (before merge)
- C) Run on PR and nightly builds

**Decision Needed:** Balance between feedback speed and CI/CD resource usage.

**Question 5: Should we implement test recording for debugging?**

**Options:**
- A) Record all tests (videos and traces)
- B) Record only failed tests
- C) Record on-demand (manual trigger)

**Decision Needed:** Balance between debugging capability and storage costs.
