# 采销经营驾驶舱数据字典 V1

## 数据分层

| 层 | 主要字段 | 要求 |
|---|---|---|
| 原始层 | `source_system`、`source_record_id`、原始 JSON、`extracted_at` | 只追加、可追溯，不覆盖原值 |
| 清洗层 | 标准类型、五时间字段、状态原值与标准值 | 记录清洗规则版本 |
| 映射层 | 仓库/渠道/SKU 等标准键、`mapping_version`、确认状态 | 未发布版本不得进入正式 KPI |
| 指标层 | 指标值、单位、口径、来源、更新时间、冲突状态、版本 | 只消费已发布映射和口径 |

## 销售事实

| 标准字段 | 类型 | 分类 | 说明 | 必填/状态 |
|---|---|---|---|---|
| `source_system` | string | 追溯 | 数据源系统，正式接入目标为吉客云 | 必填 |
| `source_record_id` | string | 业务键 | 稳定源记录 ID，禁止使用临时行号 | 待 API 确认 |
| `create_time` | datetime | 时间 | 创建时间 | 必须保留 |
| `pay_time` | datetime | 时间 | 付款时间，已确认销售主时间 | 必须保留 |
| `audit_time` | datetime | 时间 | 审核时间 | 必须保留 |
| `consign_time` | datetime | 时间 | 发货时间 | 必须保留 |
| `complete_time` | datetime | 时间 | 完成时间 | 必须保留 |
| `order_key` | string | 业务键 | 订单去重键 | BC-002 |
| `sku_source_key` | string | 维度键 | 源 SKU 标识 | 待映射发布 |
| `channel_source_key` | string | 维度键 | 源渠道/店铺标识 | 待映射发布 |
| `amount` | decimal | 指标 | 销售金额源值 | BC-001 |
| `quantity` | decimal | 指标 | 销售数量源值 | 待 API 确认 |
| `raw_status` | string | 状态 | 吉客云原始状态 | 待 API 确认 |
| `mapped_status` | string | 状态 | 已发布状态映射结果 | 待版本发布 |
| `extracted_at` | datetime | 追溯 | 抽取时间 | 必填 |
| `mapping_version` | string | 治理 | 渠道/SKU/口径发布版本 | 正式 KPI 必填 |

## 库存快照

| 标准字段 | 类型 | 分类 | 说明 | 必填/状态 |
|---|---|---|---|---|
| `source_system` | string | 追溯 | 数据源系统 | 必填 |
| `source_record_id` | string | 业务键 | 稳定源记录 ID | BC-007 |
| `snapshot_time` | datetime | 时间 | 库存快照时间 | 待 API 确认 |
| `warehouse_source_key` | string | 维度键 | 源仓库 | 待映射发布 |
| `location_source_key` | string | 维度键 | 源库位 | 待映射发布 |
| `sku_source_key` | string | 维度键 | 源 SKU | 待映射发布 |
| `physical_qty` | decimal | 指标 | 实物库存候选值 | BC-003 |
| `locked_qty` | decimal | 指标 | 锁定数量候选值 | BC-003 |
| `available_qty` | decimal | 指标 | 可销售库存候选值 | BC-003 |
| `financial_qty` | decimal | 指标 | 财务库存候选值 | BC-003 |
| `inventory_value` | decimal | 指标 | 库存金额 | BC-003 |
| `extracted_at` | datetime | 追溯 | 抽取时间 | 必填 |
| `mapping_version` | string | 治理 | 仓库/SKU/库存口径发布版本 | 正式 KPI 必填 |

## 采购与调拨

采购、调拨的源字段名不在未取得 API 文档时编造。标准层必须具备：稳定源记录 ID、单据/明细业务键、SKU、数量、源/目标仓库、原始状态、标准状态、创建/审核/出入库/关闭时间、抽取时间和映射版本。具体字段绑定分别由 BC-008、BC-009 决定。

## 敏感等级

- L1 公共：页面导航、无业务值的接口状态。
- L2 内部：已授权范围内的普通销售/库存聚合。
- L3 受限：成本、毛利、政策返点、采购金额、跨渠道汇总。
- L4 高敏：凭据、个人信息、客户/物流备注、唯一码、完整明细导出。

本轮接口不返回 L3/L4 真实字段或值。
