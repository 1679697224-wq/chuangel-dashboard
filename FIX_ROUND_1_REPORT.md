# 采销经营驾驶舱 V1 · Codex Fix Round 1 报告

## 1. 审查对象与范围

- WorkBuddy 审查对象：`b5d3c28f5f2798013abf46837c568b2c3a47d695`。
- 整改分支：`fix/caixiao-v1-review1`。
- 本轮范围：全部 P0、全部 P1；P2 仅登记，不扩展。
- `WORKBUDDY_REVIEW.md`：已检查本地仓库、远端 `main`、远端 `feat/caixiao-v1` 及工作区，均未找到该文件。本报告以 PO 消息中列明的完整 P0/P1 为整改基准，不推测缺失文件内容。
- 最终 Review 对象：以 Codex 最终交付回复中的完整提交哈希和远端分支头为准。

## 2. P0 修复

### P0-1 吉客云凭据

- 13 个被跟踪的 `dsh_keys/jky_*.py` 脚本已删除当前源码中的硬编码 AppKey/AppSecret，统一从 `JKY_APP_KEY`、`JKY_APP_SECRET` 环境变量读取。
- `caixiao/.env.example` 的 Token、初始化密码和吉客云凭据均为空占位。
- `.gitignore` 已覆盖嵌套 `.env`、credentials、secrets、证书/密钥及 `dsh_keys` 本地敏感配置。
- 新增 `CREDENTIAL_ROTATION_REQUIRED.md`，仅列需要轮换的凭据类型，不记录旧值。
- 当前源码修复不能消除 Git 历史风险；PO 仍须撤销/轮换、核查调用日志和仓库传播范围。
- 未重写 Git 历史、未强制推送、未修改仓库权限、未连接吉客云。

### P0-2 销售 ETL

- 新增销售事实表，保留 `trade_no`、`line_id`、五时间、`modified_time`、状态、数量、金额、原始仓库/渠道/门店、货号、SKU、源 API 与原始载荷引用及同步元数据。
- 同步优先使用 `modified_time` 或等同订单更新时间；不支持时采用可配置滚动回溯窗口。
- 使用 `(source_system, trade_no, line_id)` upsert，避免重跑重复。
- 同步过程不按 `pay_time` 或 `consign_time` 过滤经营期间；付款时间只由已发布 `sales_caliber` 在指标阶段应用。
- `dsh_keys/` 内保留的旧看板聚合脚本已明确隔离为旧系统维护/受控验证用途，`caixiao/backend` 不得导入；自动测试持续检查新正式链路不存在该依赖。本轮未擅自改变受保护旧看板的现网行为。
- 跨发货月付款订单自动测试通过。

## 3. P1 逐项修复

1. **订单状态复核**：只读扫描真实销售样本，观察到5个状态；生成 `caixiao/docs/SALES_STATUS_REVIEW.md`。所有裁定列保持待 PO 确认。
2. **Sandbox 差异引擎**：销售输出旧/新总额、差额、差异率、差异订单、仅旧/仅新、金额不一致及渠道/门店/SKU差异；库存输出数量、金额、仓库、SKU和映射差异。
3. **全链 KPI 门禁**：正式指标依赖事实、已发布仓库/渠道/SKU映射、销售/库存口径及销售调整规则；缺项返回“待确认”和明细清单。
4. **库存三口径**：仓库映射发布 `SPOT/IN_TRANSIT/EXCLUDE`；现货、在途、经营库存独立计算；未知仓库阻断；API→原始仓库→映射版本→分类可追溯。
5. **双WOI**：现货WOI和含在途WOI并列；默认28天但从 `sales_caliber` 读取；三个零值边界显式处理。
6. **红冲/退款/退货**：新增独立 `sales_adjustment_rules`，支持 `INCLUDE/EXCLUDE/OFFSET/PENDING`；`OFFSET` 缺 multiplier 时阻断。
7. **前端整改**：全局业务板块/品牌/渠道/日期/对比口径跨页继承；SKU搜索和详情下钻；7/14/28/90销量、现货/在途/经营库存、双WOI及渠道/仓库/价格/库龄/DG政策分别显示；缺项单独待接入。
8. **版本审计**：人工确认/发布记录 before、after、reason、affected_metrics、confirmed_by/at、published_by/at；页面可见。
9. **测试证据**：新增ETL、状态、调整、Sandbox、KPI门禁、三库存、双WOI和审计测试；生成机器可读 `caixiao/coverage.xml`。

## 4. Sandbox 验证结果

浏览器使用脱敏记录执行销售对比：旧金额100、新事实按 `pay_time` 聚合金额90，差额-10、差异率-10%，正确识别同一订单金额不一致及渠道、门店、SKU差异。响应包含：

`验证数据，不代表正式经营口径`

且 `formal_kpi_enabled=false`。该数据未写入正式 KPI。

## 5. 测试与覆盖率

- 自动测试：63项通过，0失败，0错误。
- 机器可读覆盖率：`caixiao/coverage.xml`。
- 实测覆盖率：494 / 1,301 个后端可执行语句行，37.97%。
- 旧报告的92.4%没有同等机器可读证据，本轮已纠正为可复核实际结果。
- 浏览器：PC 1280×720及移动端375×812通过；7个页面无加载失败；移动端无横向溢出；控制台 warning/error 为0。

## 6. 真实样本复核

- 销售样本 SHA-256：`5168b5a7f7546e077305b8569c6e44a43f5948f4604378d8f66d335ff57c63fe`。
- 扫描规模：11,165条商品明细、7,300个不同订单、31字段。
- 实际状态：发货在途、已完成、待发货-已递交、待复核、待审核。
- 未复制订单号、客户/客服备注、物流单号、唯一码或其他敏感明细。

## 7. 受保护文件复核

| 文件 | SHA-256 | 与审查基准差异 |
|---|---|---|
| `登录权限系统/boss-dashboard-v6.html` | `cca775b82da19564cb6b62ffbe1e8be155e472a5e712f8d86b653de9a19d87c2` | 无 |
| `登录权限系统/shure-dashboard-v6.html` | `b5961a0583fc5f0fc12d06cc33e5dde6565c9b7d3854cc080f4eb0dcf75c2ab9` | 无 |
| `登录权限系统/app.py` | `7270f020b2c9506e77c65a390068fb3b5b5bfd1223e8573e33af590c0369d8d0` | 无 |
| `登录权限系统/users.json` | `4330775cbd9f72853e4ec563d298bbaca93f38954043f02682bea007db9151e7` | 无 |
| `客流爬虫/config.json` | `c43426cd2fe037e6ff07a9bff7c724d04d6c1cac852cf8cd9b6fb0cc3662cbe5` | 无 |

## 8. 仍需 PO 确认/执行

- 完成吉客云旧凭据轮换、旧令牌撤销、权限最小化和历史访问核查。
- 核查受保护旧客流爬虫目录中的已跟踪 token 类文件；本轮按保护红线未改动、未输出其值。
- 吉客云销售API是否提供稳定 `modified` 查询、分页和源明细行ID。
- 销售状态逐项 `INCLUDE/EXCLUDE/OFFSET/PENDING` 结论。
- 销售金额字段、退款/退货/红冲符号和 `OFFSET` multiplier。
- 仓库、渠道、SKU正式映射；现货/在途识别字段；业务板块/品牌字段。
- 数据负责人、角色权限、下载/发布审批和正式接口联调责任人。

## 9. P2 延后

本轮没有新增业务页面、市场价、合同发票、完整钉钉H5或AI预测，也没有开始第二轮功能开发。

## 10. 发布限制

本提交不允许生产部署；不得在 PO 完成凭据轮换、WorkBuddy Review Round 2 通过、真实 API 契约确认和业务口径发布前进入试点或正式经营查询。
