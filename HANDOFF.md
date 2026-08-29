# HANDOFF — 采销经营驾驶舱 V1

## 交付状态

- 分支：`feat/caixiao-v1`
- 基线：GitHub `main` 提交 `0c02f7d664b9c7495609ef5b6d40d0adc01edc3e`
- 当前状态：第一轮代码与本地检查已完成，待提交并交 WorkBuddy Review
- 正式环境：未部署
- 真实数据：未连接

## 已完成

1. 独立 `caixiao/` 运行目录与环境配置。
2. 统一 `/api/v1/`、认证、权限范围、审计和安全响应头。
3. 仓库/渠道/SKU/销售口径/库存口径的待复核池、确认和发布版本机制。
4. 未确认数据阻断正式 KPI；Sandbox 只读快照检查与五时间复算。
5. 吉客云四数据域适配卡和真实接口结构，无凭据时不调用、不伪造。
6. 四个首批业务页面、映射复核、API 复核与 Sandbox 页面。

## Review 入口

- 启动说明：`caixiao/README.md`
- API 合同：`caixiao/docs/API.md`
- 数据字典：`caixiao/docs/DATA_DICTIONARY.md`
- 测试结果：`caixiao/docs/TEST_REPORT.md`
- 正式规则：`BUSINESS_RULES.md`
- 待确认：`BUSINESS_CONFIRMATION_REQUIRED.md`
- 安全发现：`SECURITY_FINDINGS.md`

## 受保护内容

本轮禁止修改的 2 份现网看板、登录后端、用户文件和客流爬虫正式配置已在开发前计算 SHA-256；完成后将再次校验。其具体哈希写入最终测试报告，便于 WorkBuddy 复核。

## 已知阻塞

- 缺吉客云 API 文档、端点、鉴权、限流、分页和稳定源记录 ID 的正式确认。
- 缺正式角色矩阵、仓库/渠道/SKU 映射和三库存细则。
- 缺 Apple 政策结构化输入及采购/调拨字段契约。
- GitHub Git 传输链路不稳定；最终提交后需再次尝试推送并记录结果。

## 下一步

停止继续扩展功能，将最终提交交给 WorkBuddy 做安全、API 契约、数据门禁、移动端和真实环境联调 Review。Review 对象使用 Codex 最终回复报告的完整提交哈希，避免对象漂移。不得自行合并 `main` 或部署生产。
