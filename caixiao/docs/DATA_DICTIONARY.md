# 采销经营驾驶舱数据字典 V1

## 数据分层

| 层 | 主要字段 | 要求 |
|---|---|---|
| 原始层 | `source_system`、`source_record_id`、原始 JSON、`extracted_at` | 只追加、可追溯，不覆盖原值 |
| 清洗层 | 标准类型、五时间字段、`modified_time`、状态原值与标准值 | 记录清洗规则版本；不得按发货窗口裁剪付款销售事实 |
| 映射层 | 仓库/渠道/SKU 等标准键、`mapping_version`、确认状态 | 未发布版本不得进入正式 KPI |
| 指标层 | 指标值、单位、口径、来源、更新时间、冲突状态、版本 | 只消费已发布映射和口径 |

## 销售事实

| 标准字段 | 类型 | 分类 | 说明 | 必填/状态 |
|---|---|---|---|---|
| `source_system` | string | 追溯 | 数据源系统，正式接入目标为吉客云 | 必填 |
| `source_record_id` | string | 业务键 | 稳定源记录 ID，禁止使用临时行号 | 待 API 确认 |
| `trade_no` | string | 业务键 | 订单编号；订单数去重候选键 | 必填/待 API 稳定性确认 |
| `line_id` | string | 业务键 | 订单商品明细稳定行键 | 必填/待 API 确认 |
| `create_time` | datetime | 时间 | 创建时间 | 必须保留 |
| `pay_time` | datetime | 时间 | 付款时间，已确认销售主时间 | 必须保留 |
| `audit_time` | datetime | 时间 | 审核时间 | 必须保留 |
| `consign_time` | datetime | 时间 | 发货时间 | 必须保留 |
| `complete_time` | datetime | 时间 | 完成时间 | 必须保留 |
| `modified_time` | datetime | 同步时间 | 接口提供时作为首选增量游标；不等于经营统计时间 | 待 API 稳定性确认 |
| `sku_raw` | string | 维度键 | 源 SKU 标识 | 待 `sku_mapping` 发布 |
| `channel_raw_name` | string | 维度键 | 源渠道/店铺标识 | 待 `channel_mapping` 发布 |
| `warehouse_raw_name` | string | 维度键 | 源发货仓库原值 | 待 `warehouse_mapping` 发布 |
| `payment` | decimal | 指标 | 销售金额源值 | BC-001 |
| `quantity` | decimal | 指标 | 销售数量源值 | 待 API 确认 |
| `trade_status` | string | 状态 | 吉客云原始状态，禁止程序直接裁定 | 必填 |
| `sales_adjustment_action` | enum | 状态规则 | `INCLUDE/EXCLUDE/OFFSET/PENDING` | 待 `sales_adjustment_rules` 发布 |
| `source_api` | string | 追溯 | 实际来源 API/方法标识 | 必填 |
| `raw_json_reference` | string | 追溯 | 原始载荷受控存储引用，不在事实表复制敏感 JSON | 必填 |
| `extracted_at` | datetime | 追溯 | 抽取时间 | 必填 |
| `synced_at` | datetime | 追溯 | 入事实层时间 | 必填 |
| `sync_job_id` | string | 追溯 | 同步任务 ID | 必填 |

## 库存快照

| 标准字段 | 类型 | 分类 | 说明 | 必填/状态 |
|---|---|---|---|---|
| `source_system` | string | 追溯 | 数据源系统 | 必填 |
| `source_record_id` | string | 业务键 | 稳定源记录 ID | BC-007 |
| `snapshot_time` | datetime | 时间 | 库存快照时间 | 待 API 确认 |
| `warehouse_raw_name` | string | 维度键 | 源仓库原值 | 待映射发布 |
| `sku_raw` | string | 维度键 | 源 SKU | 待映射发布 |
| `quantity` | decimal | 指标 | 源库存数量，不允许跨未确认仓库直接累计 | 必填 |
| `amount` | decimal | 指标 | 源库存金额 | 字段/计价待确认 |
| `inventory_class` | enum | 映射结果 | `SPOT` 现货、`IN_TRANSIT` 在途、`EXCLUDE` 排除 | 待仓库映射发布 |
| `extracted_at` | datetime | 追溯 | 抽取时间 | 必填 |
| `source_api` / `raw_json_reference` / `synced_at` / `sync_job_id` | string/datetime | 追溯 | API→原始仓库→映射版本→库存分类的追溯链 | 必填 |

## 正式 KPI 门禁

- 销售：销售事实 + 已发布仓库/渠道/SKU 映射 + 已发布 `sales_caliber` + 已发布 `sales_adjustment_rules`。
- 库存：库存事实 + 已发布仓库/SKU 映射 + 已发布 `inventory_caliber`。
- 任一源仓库、渠道、SKU 或订单状态未映射，相关 KPI 返回“待确认”和缺失清单，不输出部分正式数字。
- 现货库存：仓库映射为 `SPOT` 的数量。
- 在途库存：仓库映射为 `IN_TRANSIT` 且满足已发布 `inventory_caliber` 的数量。
- 经营库存：现货 + 符合经营规则的在途；`EXCLUDE` 不计入。
- 现货WOI与含在途WOI并列；销量窗口默认 28 天但由版本配置，零库存/零销量组合分别返回明确状态。

## 采购与调拨

采购、调拨的源字段名不在未取得 API 文档时编造。标准层必须具备：稳定源记录 ID、单据/明细业务键、SKU、数量、源/目标仓库、原始状态、标准状态、创建/审核/出入库/关闭时间、抽取时间和映射版本。具体字段绑定分别由 BC-008、BC-009 决定。

## 敏感等级

- L1 公共：页面导航、无业务值的接口状态。
- L2 内部：已授权范围内的普通销售/库存聚合。
- L3 受限：成本、毛利、政策返点、采购金额、跨渠道汇总。
- L4 高敏：凭据、个人信息、客户/物流备注、唯一码、完整明细导出。

本轮接口不返回 L3/L4 真实字段或值。
