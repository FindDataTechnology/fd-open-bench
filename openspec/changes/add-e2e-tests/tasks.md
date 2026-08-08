> **⏸️ 本 change 暂停(2026-08-08)**:`refactor-benchmark-core` 正在重构页面信息架构
> (Dashboard/CostAnalyzer/Evaluators/Login 页将被删除,新增 Leaderboard/Benchmarks 页)。
> 本 change 已完成的测试基础设施(Playwright 配置、fixtures、page objects)保留;
> 剩余测试任务将在 refactor-benchmark-core 阶段 3 页面定型后重新瞄准,相关测试用例需按新 IA 重写。

## 1. Test Infrastructure Setup

- [x] 1.1 Install Playwright and dependencies
- [x] 1.2 Create playwright.config.ts with base configuration
- [x] 1.3 Create test directory structure (pages/, fixtures/, utils/, specs/)
- [x] 1.4 Create base page object class with common methods
- [x] 1.5 Create test data fixtures (users, agents, datasets, evaluations)
- [x] 1.6 Create database seeding utilities (seedTestData, cleanupTestData)
- [x] 1.7 Create authentication utilities (loginViaApi)
- [x] 1.8 Configure test timeout and retry settings
- [x] 1.9 Configure parallel test execution (4 workers)
- [x] 1.10 Configure test reporters (HTML, JSON)

## 2. CI/CD Integration

- [x] 2.1 Create GitHub Actions workflow for e2e tests
- [x] 2.2 Configure workflow to run on pull_request events
- [x] 2.3 Add workflow steps to install dependencies
- [x] 2.4 Add workflow steps to start backend and frontend servers
- [x] 2.5 Add workflow steps to run Playwright tests
- [x] 2.6 Configure artifact upload for test results
- [x] 2.7 Configure artifact upload for screenshots and videos
- [ ] 2.8 Test workflow execution on sample PR

## 3. Authentication E2E Tests

- [x] 3.1 Create login page object (login.page.ts)
- [x] 3.2 Implement enterEmail() method
- [x] 3.3 Implement enterPassword() method
- [x] 3.4 Implement clickLogin() method
- [x] 3.5 Implement waitForDashboard() method
- [x] 3.6 Create authentication test suite (auth.spec.ts)
- [x] 3.7 Test successful login flow with valid credentials
- [x] 3.8 Test failed login flow with invalid password
- [x] 3.9 Test login form validation for empty fields
- [x] 3.10 Test logout flow
- [x] 3.11 Test session persistence across page refreshes
- [x] 3.12 Test protected route access for unauthenticated users
- [x] 3.13 Test login error handling for network failures
- [x] 3.14 Test password masking in login form

## 4. Agent Management E2E Tests

- [x] 4.1 Create agent list page object (agents-list.page.ts)
- [x] 4.2 Create agent detail page object (agent-detail.page.ts)
- [x] 4.3 Create agent create form page object (agent-create.page.ts)
- [x] 4.4 Implement agent list page methods (getAgentList, clickAgent, clickCreateAgent)
- [x] 4.5 Implement agent detail page methods (getAgentName, getAgentDescription, clickEdit, clickDelete)
- [x] 4.6 Implement agent create form methods (enterName, enterDescription, selectAdapterType, clickSubmit)
- [x] 4.7 Create agent management test suite (agents.spec.ts)
- [x] 4.8 Test viewing agent list
- [x] 4.9 Test creating new agent
- [x] 4.10 Test viewing agent details
- [ ] 4.11 Test editing agent
- [ ] 4.12 Test deleting agent
- [x] 4.13 Test create agent form validation
- [ ] 4.14 Test duplicate agent name validation
- [ ] 4.15 Test agent list pagination
- [ ] 4.16 Test agent search functionality

## 5. Dataset Management E2E Tests

- [x] 5.1 Create dataset list page object (datasets-list.page.ts)
- [x] 5.2 Create dataset detail page object (dataset-detail.page.ts)
- [x] 5.3 Create dataset create form page object (dataset-create.page.ts)
- [x] 5.4 Implement dataset list page methods (getDatasetList, clickDataset, clickCreateDataset)
- [x] 5.5 Implement dataset detail page methods (getDatasetName, getGoldenList, clickImportGoldens)
- [x] 5.6 Implement dataset create form methods (enterName, enterDescription, clickSubmit)
- [x] 5.7 Create dataset management test suite (datasets.spec.ts)
- [x] 5.8 Test viewing dataset list
- [x] 5.9 Test creating new dataset
- [x] 5.10 Test viewing dataset details
- [ ] 5.11 Test viewing golden list
- [ ] 5.12 Test importing goldens from JSON
- [ ] 5.13 Test importing invalid JSON validation
- [ ] 5.14 Test editing dataset
- [ ] 5.15 Test deleting dataset
- [x] 5.16 Test create dataset form validation
- [ ] 5.17 Test duplicate dataset name validation

## 6. Evaluation Workflow E2E Tests

- [ ] 6.1 Create evaluation list page object (evaluations-list.page.ts)
- [ ] 6.2 Create evaluation detail page object (evaluation-detail.page.ts)
- [ ] 6.3 Create evaluation create form page object (evaluation-create.page.ts)
- [ ] 6.4 Implement evaluation list page methods (getEvaluationList, clickEvaluation, clickCreateEvaluation)
- [ ] 6.5 Implement evaluation detail page methods (getEvaluationStatus, getResultsList, clickViewTrace)
- [ ] 6.6 Implement evaluation create form methods (selectAgent, selectDataset, selectEvaluators, clickSubmit)
- [ ] 6.7 Create evaluation workflow test suite (evaluations.spec.ts)
- [ ] 6.8 Test viewing evaluation list
- [ ] 6.9 Test creating new evaluation
- [ ] 6.10 Test monitoring evaluation progress in real-time
- [ ] 6.11 Test viewing evaluation results
- [ ] 6.12 Test viewing evaluation trace
- [ ] 6.13 Test cancelling running evaluation
- [ ] 6.14 Test retrying failed evaluation
- [ ] 6.15 Test exporting evaluation results as CSV
- [ ] 6.16 Test evaluation status filtering
- [ ] 6.17 Test evaluation sorting
- [ ] 6.18 Test evaluation progress WebSocket updates

## 7. Evaluator Configuration E2E Tests

- [ ] 7.1 Create evaluator list page object (evaluators-list.page.ts)
- [ ] 7.2 Create evaluator detail page object (evaluator-detail.page.ts)
- [ ] 7.3 Create evaluator create form page object (evaluator-create.page.ts)
- [ ] 7.4 Implement evaluator list page methods (getEvaluatorList, clickEvaluator, clickCreateEvaluator)
- [ ] 7.5 Implement evaluator detail page methods (getEvaluatorName, getEvaluatorType, clickTest)
- [ ] 7.6 Implement evaluator create form methods (enterName, selectType, enterConfig, clickSubmit)
- [ ] 7.7 Create evaluator configuration test suite (evaluators.spec.ts)
- [ ] 7.8 Test viewing evaluator list
- [ ] 7.9 Test creating new validator evaluator
- [ ] 7.10 Test creating new LLM judge evaluator
- [ ] 7.11 Test creating new executor evaluator
- [ ] 7.12 Test testing evaluator with sample input/output
- [ ] 7.13 Test editing evaluator
- [ ] 7.14 Test deleting evaluator
- [ ] 7.15 Test evaluator config validation
- [ ] 7.16 Test evaluator type filtering
- [ ] 7.17 Test evaluator search functionality

## 8. Cost Analysis E2E Tests

- [ ] 8.1 Create cost analyzer page object (cost-analyzer.page.ts)
- [ ] 8.2 Implement cost analyzer page methods (selectAgent, selectDateRange, getCostBreakdown, getRoiTrends)
- [ ] 8.3 Create cost analysis test suite (cost-analyzer.spec.ts)
- [ ] 8.4 Test viewing cost analyzer page
- [ ] 8.5 Test selecting agent for cost analysis
- [ ] 8.6 Test selecting date range
- [ ] 8.7 Test viewing cost breakdown pie chart
- [ ] 8.8 Test viewing ROI trends line chart
- [ ] 8.9 Test viewing daily costs bar chart
- [ ] 8.10 Test viewing cost summary statistics
- [ ] 8.11 Test comparing agents cost
- [ ] 8.12 Test exporting cost analysis data
- [ ] 8.13 Test cost analysis with no data
- [ ] 8.14 Test cost analysis loading state
- [ ] 8.15 Test cost analysis error handling

## 9. Test Data Management

- [ ] 9.1 Create user factory function (createUser)
- [ ] 9.2 Create agent factory function (createAgent)
- [ ] 9.3 Create dataset factory function (createDataset)
- [ ] 9.4 Create golden factory function (createGolden)
- [ ] 9.5 Create evaluation factory function (createEvaluation)
- [ ] 9.6 Create evaluator factory function (createEvaluator)
- [ ] 9.7 Implement test data seeding before test suites
- [ ] 9.8 Implement test data cleanup after test suites
- [ ] 9.9 Implement database transaction isolation for tests
- [ ] 9.10 Test data management utilities

## 10. Test Optimization

- [ ] 10.1 Optimize test execution speed
- [ ] 10.2 Implement API shortcuts for non-auth tests
- [ ] 10.3 Configure test parallelization
- [ ] 10.4 Implement test caching for dependencies
- [ ] 10.5 Set up test timeout limits (30s per test)
- [ ] 10.6 Implement retry logic for flaky tests (max 2 retries)
- [ ] 10.7 Monitor test execution time
- [ ] 10.8 Identify and fix slow tests

## 11. Test Documentation

- [ ] 11.1 Create e2e test README
- [ ] 11.2 Document how to run e2e tests locally
- [ ] 11.3 Document how to write new e2e tests
- [ ] 11.4 Document page object model pattern
- [ ] 11.5 Document test data management
- [ ] 11.6 Document CI/CD integration
- [ ] 11.7 Document troubleshooting common issues
- [ ] 11.8 Create test maintenance guide

## 12. Test Coverage & Reporting

- [ ] 12.1 Set up test coverage reporting
- [ ] 12.2 Configure HTML test reporter
- [ ] 12.3 Configure JSON test reporter
- [ ] 12.4 Set up screenshot capture on failure
- [ ] 12.5 Set up video recording for all tests
- [ ] 12.6 Set up trace viewer for debugging
- [ ] 12.7 Configure test result artifacts in CI/CD
- [ ] 12.8 Monitor test coverage metrics

## 13. Frontend Test Hooks

- [ ] 13.1 Add data-testid attributes to login page
- [ ] 13.2 Add data-testid attributes to dashboard page
- [ ] 13.3 Add data-testid attributes to agent pages
- [ ] 13.4 Add data-testid attributes to dataset pages
- [ ] 13.5 Add data-testid attributes to evaluation pages
- [ ] 13.6 Add data-testid attributes to evaluator pages
- [ ] 13.7 Add data-testid attributes to cost analyzer page
- [ ] 13.8 Add data-testid attributes to settings page

## 14. Integration Testing

- [ ] 14.1 Test e2e tests with SQLite database
- [ ] 14.2 Test e2e tests with PostgreSQL database
- [ ] 14.3 Test e2e tests in headless mode
- [ ] 14.4 Test e2e tests in headed mode (for debugging)
- [ ] 14.5 Test e2e tests with different browsers (Chromium, Firefox, WebKit)
- [ ] 14.6 Test e2e tests in CI/CD environment
- [ ] 14.7 Test e2e tests with parallel execution
- [ ] 14.8 Verify all tests pass consistently

## 15. Final Verification

- [ ] 15.1 Run full e2e test suite
- [ ] 15.2 Verify >80% test coverage for critical paths
- [ ] 15.3 Verify all tests pass in CI/CD
- [ ] 15.4 Verify test execution time < 10 minutes
- [ ] 15.5 Verify test artifacts are uploaded correctly
- [ ] 15.6 Verify test documentation is complete
- [ ] 15.7 Train team on writing e2e tests
- [ ] 15.8 Get team feedback on test infrastructure
