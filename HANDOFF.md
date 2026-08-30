# HANDOFF — 采销经营驾驶舱 V1 Fix Round 1

## 交付状态

- Review 基准提交：`b5d3c28f5f2798013abf46837c568b2c3a47d695`。
- 整改分支：`fix/caixiao-v1-review1`。
- 状态：全部 P0 和 P1 已完成本地整改与验证，待 WorkBuddy Review Round 2。
- Review 对象：以 Codex 最终回复中的完整提交哈希及远端 `fix/caixiao-v1-review1` 分支头为准，避免同一提交回写自身哈希。
- `main`：未合并、未移动。
- 正式环境：未部署。
- 吉客云生产接口：未连接。

## P0 完成

1. 当前 `dsh_keys/` 脚本中的吉客云 AppKey/AppSecret 已改为环境变量读取；未在输出、测试或文档复述旧值。
2. `.env.example` 仅保留空占位，`.gitignore` 增加 `.env`、credentials、secrets 和 `dsh_keys` 本地敏感配置规则。
3. 新增 `CREDENTIAL_ROTATION_REQUIRED.md`；明确 PO 仍必须撤销/轮换旧凭据并核查 Git 历史风险。
4. 新销售 ETL 使用 `modified_time` 或等同更新时间增量；不稳定时采用滚动回溯 + `(source_system, trade_no, line_id)` upsert。
5. 同步范围与经营统计口径分离；`consign_time` 不再决定付款销售事实是否入库，`pay_time` 由发布后的 `sales_caliber` 读取。
6. `dsh_keys/` 旧聚合脚本仅保留用于旧系统维护/受控验证，禁止接入新正式链路；隔离规则及自动测试已建立，未改变受保护旧看板现网行为。

## P1 完成

- 销售/库存事实表、同步状态、全链路追溯字段。
- 脱敏销售状态 distinct 扫描及《销售状态复核清单》；程序不自行裁定状态。
- `sales_adjustment_rules` 的 `INCLUDE/EXCLUDE/OFFSET/PENDING` 结构和发布门禁。
- 销售及库存真实 Sandbox 差异引擎，统一显示“验证数据，不代表正式经营口径”。
- 事实 → 仓库/渠道/SKU映射 → 销售/库存口径 → 正式 KPI 的全链门禁。
- 现货、在途、经营库存三口径，未知仓库和缺失分类阻断。
- 现货WOI、含在途WOI，默认28天可配置及三个零值边界。
- 全局筛选跨页继承、SKU搜索/详情、首页门禁指标、复核审计字段、Sandbox交互。

## 测试与检查

- 自动测试：63 项通过，0 失败，0 错误。
- 覆盖率：494 / 1,301 个后端可执行语句行，37.97%；机器可读报告 `caixiao/coverage.xml`。
- 浏览器：PC 与 375px 移动端通过；7个页面可访问；无横向溢出；控制台 warning/error 为 0。
- Sandbox：脱敏示例实际返回总额、差异率、差异订单、渠道、门店和SKU差异。
- 当前未生成任何正式经营数字，未连接真实系统。

## 待 PO / WorkBuddy

- 立即完成吉客云历史凭据撤销、轮换、日志核查及仓库传播范围评估。
- 确认受保护旧客流爬虫目录中的已跟踪 token 类文件是否仍有效；如有效另行轮换和迁移。
- 提供并确认吉客云 API 文档、鉴权、分页、限流、稳定 `modified` 字段和稳定明细行 ID。
- 对 `caixiao/docs/SALES_STATUS_REVIEW.md` 的每个源状态发布人工结论。
- 确认销售金额字段、退款/退货/红冲符号和 `OFFSET` multiplier。
- 确认仓库、渠道、SKU映射及库存口径；当前没有任何默认公司映射。
- `WORKBUDDY_REVIEW.md` 在本地和远端分支均未找到；本轮以 PO 消息列明的全部 P0/P1 作为整改基准。

## 延后 P2

本轮没有新增业务页面、市场价、合同发票、完整钉钉H5或AI预测。以上继续留待单独授权。

## 下一步

停止开发，将最终提交交给 WorkBuddy 执行 Review Round 2。不得自行合并 `main` 或部署生产。
