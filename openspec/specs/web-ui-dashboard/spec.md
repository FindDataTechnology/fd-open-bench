# web-ui-dashboard Specification

## Purpose
TBD - created by archiving change fd-open-bench. Update Purpose after archive.
## Requirements
### Requirement: Web UI provides real-time monitoring dashboard
Web UI 首页 SHALL 为 Leaderboard 对比视图(取代原有 Dashboard),提供 benchmark 选择、对比表格、排序与钻取。批量评测进度通过轮询更新。

#### Scenario: 首页即对比榜
- **WHEN** 用户访问 `/`
- **THEN** 显示 Leaderboard 页面(benchmark 选择器 + 对比表格),而非原 Dashboard

### Requirement: Web UI provides trace explorer with tree and timeline views
The web UI SHALL provide a trace explorer that visualizes agent execution traces. The explorer SHALL support two views: tree view (hierarchical display of spans with parent-child relationships, showing span type, name, duration, token usage, and status) and timeline view (Gantt chart showing span execution over time with parallel execution visible). The explorer SHALL allow expanding/collapsing spans, filtering by span type, and searching by span name.

#### Scenario: Tree view of agent trace
- **WHEN** a user opens the trace explorer for an evaluation result
- **THEN** the UI SHALL display a tree with the root agent span, nested LLM and tool spans, each showing name, duration_ms, token_usage (for LLM spans), and status (color-coded: green=success, red=error, yellow=timeout)

#### Scenario: Timeline view of agent trace
- **WHEN** a user switches to timeline view
- **THEN** the UI SHALL display a Gantt chart with time on the x-axis, spans on the y-axis, and horizontal bars showing span duration, with parallel spans visible

#### Scenario: Expand/collapse span details
- **WHEN** a user clicks on a span in the tree view
- **THEN** the UI SHALL expand to show span details: input, output, metadata, token_usage (for LLM spans), and error details (if status=error)

### Requirement: Web UI provides evaluation configuration interface
The web UI SHALL provide an evaluation configuration interface with three modes: visual builder (no-code, form-based configuration for validators and simple LLM judges), code editor (Python syntax highlighting, for custom evaluators), and YAML config (text editor with syntax highlighting and validation). The interface SHALL support testing evaluators on sample inputs before saving.

#### Scenario: Visual builder for regex validator
- **WHEN** a user selects "Add Validator" → "Regex" in the visual builder
- **THEN** the UI SHALL display a form with fields: name, pattern, flags, must_match, and a "Test" button

#### Scenario: Test evaluator on sample input
- **WHEN** a user clicks "Test" after configuring an evaluator
- **THEN** the UI SHALL prompt for sample input, run the evaluator, and display the result (score, passed, reason)

#### Scenario: YAML config validation
- **WHEN** a user enters YAML config in the text editor
- **THEN** the UI SHALL validate the YAML in real-time, highlight syntax errors, and display validation messages

### Requirement: Web UI supports authentication and multi-user access
Web UI SHALL NOT 要求登录(内部工具定位)。后端 API SHALL 支持可选的单 token 头校验:设置 `FD_BENCH_API_TOKEN` 时校验请求头,未设置时放行。

#### Scenario: 免登录访问
- **WHEN** 用户直接访问任意前端路由
- **THEN** 不出现登录页,直接进入对应页面

#### Scenario: 可选 token 保护
- **WHEN** 后端配置 FD_BENCH_API_TOKEN=secret 且请求缺少对应头
- **THEN** API 返回 401;前端本地开发默认不配置、不受影响

### Requirement: Web UI is responsive and accessible
The web UI SHALL be responsive (usable on desktop, tablet, and mobile screens). The web UI SHALL meet WCAG 2.1 AA accessibility standards: keyboard navigation, screen reader support, sufficient color contrast, and focus indicators. The web UI SHALL support dark mode and light mode themes.

#### Scenario: Mobile responsiveness
- **WHEN** a user accesses the web UI on a mobile device (screen width < 768px)
- **THEN** the UI SHALL adapt the layout: navigation menu becomes a hamburger menu, charts stack vertically, tables become scrollable horizontally

#### Scenario: Keyboard navigation
- **WHEN** a user navigates the UI using only the keyboard (Tab, Enter, Escape)
- **THEN** all interactive elements (buttons, links, form fields) SHALL be focusable and operable via keyboard

