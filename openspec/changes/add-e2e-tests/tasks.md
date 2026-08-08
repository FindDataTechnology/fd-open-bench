> **🎯 本 change 已按新 IA 重新瞄准(2026-08-08)**:`refactor-benchmark-core` 已完成页面重构
> (Login/Dashboard/CostAnalyzer/Evaluators 页已删除,新增 Leaderboard/Benchmarks/Batch 详情页,移除多用户 auth)。
> 原 §3(认证)、§6(旧评测流)、§7(Evaluator 页)、§8(Cost Analyzer)、§13.1/13.2/13.6/13.7 作废,已删除;
> 新增 §3a(Leaderboard)、§3b(Benchmarks)、§3c(Batch 详情) 按新 IA 编写。
> 已完成的测试基础设施(§1/§2)与 Agents(§4)/Datasets(§5) 页面测试保留——这些页面仍然存在。

## 1. Test Infrastructure Setup

- [x] 1.1 Install Playwright and dependencies
- [x] 1.2 Create playwright.config.ts with base configuration
- [x] 1.3 Create test directory structure (pages/, fixtures/, utils/, specs/)
- [x] 1.4 Create base page object class with common methods
- [x] 1.5 Create test data fixtures (users, agents, datasets, evaluations)
- [x] 1.6 Create database seeding utilities (seedTestData, cleanupTestData)
- [x] 1.7 Create authentication utilities (loginViaApi) — ⚠️ auth 已移除,改造为可选 token header
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

## 3a. Leaderboard E2E Tests(新首页 `/`)

- [ ] 3a.1 Create leaderboard page object (leaderboard.page.ts): benchmark 选择器、排序、行钻取
- [ ] 3a.2 Test leaderboard empty state(无 benchmark / 无数据提示)
- [ ] 3a.3 Test selecting a benchmark loads its table(技术列 + 商业列)
- [ ] 3a.4 Test sorting by cost_per_success / roi / success_rate
- [ ] 3a.5 Test 商业列空态文案(缺 human_cost 显示"补全人工成本数据后可用"而非 0)
- [ ] 3a.6 Test clicking an agent row navigates to batch/run detail

## 3b. Benchmarks E2E Tests(`/benchmarks`)

- [ ] 3b.1 Create benchmarks list page object + detail page object
- [ ] 3b.2 Test creating a benchmark(选 dataset、勾 metric suite、填 value_formula/time_value_rate)
- [ ] 3b.3 Test value_formula 语法校验提示(非法表达式被拒)
- [ ] 3b.4 Test benchmark detail shows goldens with business fields(business_value/human_cost/human_minutes)
- [ ] 3b.5 Test "运行新批量"入口:选 agents → 提交 → 跳转 batch 详情

## 3c. Batch/Run Detail E2E Tests(`/runs/:batchId`)

- [ ] 3c.1 Create batch detail page object: 多 agent 进度、逐 golden 结果、trace 查看
- [ ] 3c.2 Test batch progress updates per agent
- [ ] 3c.3 Test per-golden results rendering(status/metric scores/cost)
- [ ] 3c.4 Test trace viewer opens for a result

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
- [ ] 4.17 Test pricing config editing(驱动商业指标准确性)

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
- [ ] 5.12 Test importing goldens from JSON(含 business_value/human_cost/human_minutes 字段)
- [ ] 5.13 Test importing invalid JSON validation
- [ ] 5.14 Test editing dataset
- [ ] 5.15 Test deleting dataset
- [x] 5.16 Test create dataset form validation
- [ ] 5.17 Test duplicate dataset name validation
- [ ] 5.18 Test golden 编辑界面商业字段读写

## 6. Test Data Management

- [ ] 6.1 Create agent factory function (createAgent)
- [ ] 6.2 Create dataset factory function (createDataset)
- [ ] 6.3 Create golden factory function (createGolden,含商业字段)
- [ ] 6.4 Create benchmark factory function (createBenchmark)
- [ ] 6.5 Create batch/run factory function (createBatch)
- [ ] 6.6 Implement test data seeding before test suites
- [ ] 6.7 Implement test data cleanup after test suites
- [ ] 6.8 Implement database transaction isolation for tests
- [ ] 6.9 删除 user factory 与 loginViaApi 依赖(auth 已移除)

## 7. Test Optimization

- [ ] 7.1 Optimize test execution speed
- [ ] 7.2 Implement API shortcuts for test setup(直接调 REST 造数据)
- [ ] 7.3 Configure test parallelization
- [ ] 7.4 Implement test caching for dependencies
- [ ] 7.5 Set up test timeout limits (30s per test)
- [ ] 7.6 Implement retry logic for flaky tests (max 2 retries)
- [ ] 7.7 Monitor test execution time
- [ ] 7.8 Identify and fix slow tests

## 8. Test Documentation

- [ ] 8.1 Create e2e test README
- [ ] 8.2 Document how to run e2e tests locally
- [ ] 8.3 Document how to write new e2e tests
- [ ] 8.4 Document page object model pattern
- [ ] 8.5 Document test data management
- [ ] 8.6 Document CI/CD integration
- [ ] 8.7 Document troubleshooting common issues
- [ ] 8.8 Create test maintenance guide

## 9. Test Coverage & Reporting

- [ ] 9.1 Set up test coverage reporting
- [ ] 9.2 Configure HTML test reporter
- [ ] 9.3 Configure JSON test reporter
- [ ] 9.4 Set up screenshot capture on failure
- [ ] 9.5 Set up video recording for failed tests
- [ ] 9.6 Set up trace viewer for debugging
- [ ] 9.7 Configure test result artifacts in CI/CD
- [ ] 9.8 Monitor test coverage metrics

## 10. Frontend Test Hooks

- [ ] 10.1 Add data-testid attributes to Leaderboard page(benchmark 选择器/表格/排序按钮/空态)
- [ ] 10.2 Add data-testid attributes to Benchmarks 列表/创建/详情页(含 Run New Batch 表单)
- [ ] 10.3 Add data-testid attributes to agent pages
- [ ] 10.4 Add data-testid attributes to dataset pages(含 golden 商业字段输入)
- [ ] 10.5 Add data-testid attributes to Batch 详情页(进度/结果表/trace)
- [ ] 10.6 Add data-testid attributes to settings page

## 11. Integration Testing

- [ ] 11.1 Test e2e tests with SQLite database(唯一支持的存储)
- [ ] 11.2 Test e2e tests in headless mode
- [ ] 11.3 Test e2e tests in headed mode (for debugging)
- [ ] 11.4 Test e2e tests with Chromium(其余浏览器可选)
- [ ] 11.5 Test e2e tests in CI/CD environment
- [ ] 11.6 Test e2e tests with parallel execution
- [ ] 11.7 Verify all tests pass consistently

## 12. Final Verification

- [ ] 12.1 Run full e2e test suite
- [ ] 12.2 Verify critical paths covered: 建 benchmark → 跑批量 → 看榜 → 钻取详情
- [ ] 12.3 Verify all tests pass in CI/CD
- [ ] 12.4 Verify test execution time < 10 minutes
- [ ] 12.5 Verify test artifacts are uploaded correctly
- [ ] 12.6 Verify test documentation is complete
