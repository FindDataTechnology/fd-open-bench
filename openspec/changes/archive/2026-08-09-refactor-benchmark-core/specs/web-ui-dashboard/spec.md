## MODIFIED Requirements

### Requirement: Web UI provides real-time monitoring dashboard
Web UI 首页 SHALL 为 Leaderboard 对比视图(取代原有 Dashboard),提供 benchmark 选择、对比表格、排序与钻取。批量评测进度通过轮询更新。

#### Scenario: 首页即对比榜
- **WHEN** 用户访问 `/`
- **THEN** 显示 Leaderboard 页面(benchmark 选择器 + 对比表格),而非原 Dashboard

### Requirement: Web UI supports authentication and multi-user access
Web UI SHALL NOT 要求登录(内部工具定位)。后端 API SHALL 支持可选的单 token 头校验:设置 `FD_BENCH_API_TOKEN` 时校验请求头,未设置时放行。

#### Scenario: 免登录访问
- **WHEN** 用户直接访问任意前端路由
- **THEN** 不出现登录页,直接进入对应页面

#### Scenario: 可选 token 保护
- **WHEN** 后端配置 FD_BENCH_API_TOKEN=secret 且请求缺少对应头
- **THEN** API 返回 401;前端本地开发默认不配置、不受影响

## REMOVED Requirements

### Requirement: Web UI provides cost analyzer with ROI visualization
**Reason**: 独立 CostAnalyzer 页并入 Leaderboard 商业列与 batch 详情页,不再单独存在。
**Migration**: ROI/成本数据由 leaderboard 与 batch 详情接口提供。

### Requirement: Web UI provides historical analysis with A/B testing
**Reason**: A/B 测试语义由"同 benchmark 多 agent 批量对比"正式取代,不再维护独立的历史分析页。
**Migration**: 历史 run 数据保留,通过 benchmark leaderboard(含历史 batch)查看。
