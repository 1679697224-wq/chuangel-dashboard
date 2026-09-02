# 采销经营驾驶舱 V2.0 销售口径专项审计

审计日期：2026-09-02
审计范围：当前 `caixiao/` 正式框架、`dsh_keys/` 历史取数链、吉客云销售导出和历史聚合结果。
结论边界：不修改既有口径，不连接吉客云，不把程序建议当业务决定。

## 1. 当前真实现状

| 项目 | 当前结论 | 证据 |
|---|---|---|
| 正式销售事实 | 未接入，0 条 | `caixiao/runtime/caixiao.sqlite3.sales_facts` |
| V1.5 正式 API | 有接口和人工门禁框架，无真实事实 | `caixiao/backend/services/metrics.py` |
| 历史吉客云 API | 存在曾实际运行的签名、分页和取数脚本 | `dsh_keys/jky_client.py`、`jky_pull.py`、`pull_api_828.py` |
| 当前真实样本 | 11,165 条订单商品明细，7,300 个订单，526 个货品 | `吉客云数据/销售单明细账.xlsx` |
| 当前销售主时间规则 | 已确认使用 `pay_time`，但必须由发布的 `sales_caliber` 应用 | `BUSINESS_RULES.md` BR-001、BR-009 |
| 状态/退款规则 | 尚未逐状态发布 | BR-002、BR-010；`BUSINESS_CONFIRMATION_REQUIRED.md` BC-017/018 |
| 正式金额字段 | 当前仓库规则仍未确认 | BC-001/018 |

## 2. 同步时间与统计时间检查

### 2.1 历史链路的真实行为

`dsh_keys/jky_pull.py` 和 `pull_api_828.py` 使用：

- 拉取窗口：`startConsignTime` / `endConsignTime`；
- 拉取字段：包括 `consignTime` 和 `payTime`；
- 后续聚合：`agg_api_828.py`、`agg_api_final.py` 再按 `payTime` 过滤/归属；部分更早脚本在 `payTime` 为空时回退 `consignTime`。

因此历史链路确实存在：

> 先由发货时间决定订单是否进入数据集，再由付款时间决定销售归属。

这会漏掉“本期付款、跨期发货”或仍未发货的订单；也可能因回溯窗口不足漏掉后续退款和状态变化。该历史逻辑不得成为 V2 正式销售数据源。

### 2.2 当前 `caixiao/` 新框架

`caixiao/backend/etl.py` 已将同步和统计分离：

- 首选按 `modified_time` 或同等订单更新时间增量；
- 若接口不稳定支持，则使用滚动回溯窗口；
- 按 `(source_system, trade_no, line_id)` upsert；
- 不在同步阶段按 pay/consign 过滤；
- 事实层保留 create/pay/audit/consign/complete/modified；
- 经营指标由已发布 `sales_caliber.time_field` 选择统计时间。

但这仍是**设计已完成、真实接口未验证**。当前适配器只有通用端点配置和请求能力，没有已核验的吉客云方法、modified 参数、分页返回结构、行级 ID 和字段映射。

### 2.3 真实导出样本观察

| 检查项 | 只读结果 | 对正式合同的影响 |
|---|---:|---|
| 明细行 | 11,165 | 粒度是订单商品明细，不是一单一行 |
| 不同订单 | 7,300 | 订单数必须按稳定订单键去重 |
| 下单时间范围 | 2026-08-01 00:02:02 ~ 2026-08-26 16:16:14 | 可作辅助审计时间 |
| 付款时间范围 | 2026-08-01 00:02:41 ~ 2026-08-26 16:16:15 | 已确认的经营主时间候选 |
| 发货时间范围 | 2026-08-01 09:58:53 ~ 2026-08-26 16:16:14 | 只能作为履约时间，不得承载付款销售同步范围 |
| 付款时间为空 | 108 行 | 必须阻断或按状态进入待复核，不得回退发货时间 |
| 发货时间为空 | 285 行 | 已付款未发货事实不能因缺发货时间丢失 |
| 本样本付款/发货跨月 | 0 行 | 只说明本次 8 月快照未观察到，不能证明历史窗口安全 |
| 负数量 | 993 行 | 需要退款/退货/冲抵业务类型和调整规则 |
| 负分摊后金额 | 620 行 | 不能仅凭符号推断退款类型 |
| 零数量 | 28 行 | 需识别服务、赠品或异常行 |
| 零分摊后金额 | 2,489 行 | 可能含赠品/权益/折让，必须有正式规则 |
| 分摊后金额与金额不一致 | 720 行 | 正式金额字段选择会直接改变 KPI |

## 3. 当前订单状态扫描

以下为真实导出中 `订单状态` 的 distinct 结果，只展示订单明细行数量，不展示具体订单或金额：

| raw_trade_status | 明细行数 | 当前正式规则 | 程序建议边界 | 是否可进入正式销售 |
|---|---:|---|---|---|
| 已完成 | 10,020 | 未逐状态发布 | 建议进入 INCLUDE/其他动作复核 | 否，待 PO 发布 |
| 发货在途 | 860 | 未逐状态发布 | 建议与已付款、履约展示分组联合复核 | 否，待 PO 发布 |
| 待审核 | 202 | BR-002 要求与已付款分开呈现 | 建议单列，不静默并入 | 否，待 PO 发布 |
| 待发货-已递交 | 78 | 未逐状态发布 | 建议核对是否等同已付款未发货 | 否，待 PO 发布 |
| 待复核 | 5 | 未逐状态发布 | 默认 PENDING | 否 |

本样本未观察到同名“取消、退款、退货、红冲、补发、调拨、3PP、分销、Shure京东补货”状态；这不表示这些业务不存在。渠道/订单类型和状态必须联合识别，新状态默认 `PENDING`。

## 4. 销售事实合同最低要求

### 4.1 建议业务键

- 订单头：优先保存吉客云稳定 `source_record_id/trade_id`，并保留 `trade_no`；
- 订单行：必须取得稳定 `line_id`。如果 API 没有稳定行 ID，PHASE 1 不得用 Excel 行号替代，应由接口负责人确认可重放的组合键；
- upsert：`source_system + source_record_id/稳定订单行键`；
- 所有原始名称保留，不在 RAW 层覆盖。

### 4.2 强制字段

| 类型 | 字段 |
|---|---|
| 主键/追溯 | source_system、source_record_id、trade_no、line_id、source_api、raw_json_reference、extracted_at、synced_at、sync_job_id |
| 时间 | create_time、pay_time、audit_time、consign_time、complete_time、modified_time |
| 业务 | trade_status、order_type、channel_raw_code/name、shop_raw_code/name、warehouse_raw_code/name、goods_no、sku_raw、quantity |
| 金额 | payment/分摊后金额候选、原金额、成本、毛利、税口径标识、币种 |
| 调整 | adjustment_type、original_trade_no/line_id、源正负号、发布的 adjustment_rule_version |

Excel 样本目前缺少 audit、complete、modified、稳定 line_id、源记录 ID、同步元数据和明确订单类型，因此只能用于复核，不足以成为长期正式合同。

## 5. 逐项业务口径状态

| 口径 | 当前现状 | 状态 |
|---|---|---|
| 销售统计主时间 | 全局使用 `pay_time` 已确认；同步窗口必须与统计口径分离 | 已确认，但 API 字段需联调 |
| 销售额含税/未税 | 样本同时有分摊后金额、成本、未税毛利/率，未见税额拆分 | 待 PO/财务确认 |
| 正式销售金额字段 | 分摊后金额与金额 720 行不一致 | 待 PO/财务确认 |
| 退款/退货/红冲 | 只允许 INCLUDE/EXCLUDE/OFFSET/PENDING；本样本没有同名状态 | 待逐类型、逐符号确认 |
| 取消订单 | 样本未观察到；不能默认排除 | 待确认 |
| 跨月退货 | 当前无可追溯关联规则 | 待确认归属原销售月还是发生月，建议两者均保留 |
| 赠品/零金额 | 2,489 行零分摊后金额，缺赠品标识 | 待确认；默认不自行计销售额/销量 |
| 内部调拨 | 当前仅能从渠道/仓库名称猜测，缺正式订单类型 | 待确认；建议与销售域隔离 |
| Shure 京东补货 | BR-005 已确认负数冲抵且不作为销售 | 已确认原则；识别字段待发布 |
| Apple线下/Apple电商/Shure | 主时间可共用 pay_time；状态、金额、退款和特殊业务不得默认完全相同 | 需要适用范围版本 |

## 6. 推荐但未执行的 PHASE 1 销售链

1. 取得只读 API 文档和最小权限测试环境，核验订单头/行接口、modified、分页和稳定 ID。
2. 用 3~7 天滚动回溯加 upsert 与 `modified_time` 主增量并行验证，禁止发货时间窗口。
3. 导入不带敏感备注的订单行原始引用，保留六类时间和源状态。
4. 对 5 个已观察状态及新增状态生成复核清单。
5. 发布 sales_caliber、sales_adjustment_rules、channel/store/warehouse/SKU 映射后再出 KPI。
6. 用 2026-08 Excel 快照与旧聚合 JSON 做 Sandbox 对账，不把其值并入正式事实。

需要 PO 的最少决定已集中在 `DATA_CONFIRMATION_REQUIRED_V2.md`，技术联调风险见 `DATA_CALIBER_CONFIRMATION_REQUIRED_V2.md`。
