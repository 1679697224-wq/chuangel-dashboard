# 采销经营驾驶舱 API V1

基础路径：`/api/v1/`。除健康检查和登录外，接口必须使用 HttpOnly 会话 Cookie 或 `Authorization: Bearer <token>` 鉴权。

## 正式接口

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| GET | `/api/v1/health` | 公开 | 存活检查，不返回环境详情或凭据 |
| POST | `/api/v1/auth/login` | 公开 | 登录，5 次失败后临时阻断 |
| POST | `/api/v1/auth/logout` | 已登录 | 撤销服务端会话 |
| GET | `/api/v1/auth/me` | `dashboard:view` | 当前账号、功能权限和数据范围 |
| GET | `/api/v1/system/context` | `dashboard:view` | 当前 FORMAL/DEMO 模式、数据隔离与筛选选项 |
| GET | `/api/v1/dim/boards` | `dashboard:view` | 看板模块 |
| GET | `/api/v1/dim/channels` | `dashboard:view` | 仅已发布渠道映射 |
| GET | `/api/v1/dim/warehouses` | `dashboard:view` | 仅已发布仓库映射 |
| GET | `/api/v1/dim/skus` | `dashboard:view` | 仅已发布 SKU 映射 |
| GET | `/api/v1/sales/summary` | `dashboard:view` | 销售核心指标 |
| GET | `/api/v1/sales/daily` | `dashboard:view` | 销售日趋势 |
| GET | `/api/v1/sales/sku/{sku}` | `dashboard:view` | SKU 销售视图 |
| GET | `/api/v1/sales/status-review` | `dashboard:view` | 源订单状态聚合复核清单，程序不自动裁定 |
| GET | `/api/v1/sync/sales/plan` | `dashboard:view` | modified 增量或滚动回溯 upsert 同步计划 |
| GET | `/api/v1/inventory/summary` | `dashboard:view` | 三库存视图总览 |
| GET | `/api/v1/inventory/aging` | `dashboard:view` | 库龄明细 |
| GET | `/api/v1/purchase/summary` | `dashboard:view` | 采购与在途 |
| GET | `/api/v1/policy/summary` | `dashboard:view` | Apple 政策经营 |
| GET | `/api/v1/anomaly/list` | `dashboard:view` | 经营异常 |
| GET | `/api/v1/action/list` | `dashboard:view` | 待确认经营动作 |
| GET | `/api/v1/traffic/summary` | `dashboard:view` | APR客流统一输入合同：date/store/traffic/source/updated_at |
| GET | `/api/v1/metrics/dict` | `dashboard:view` | 指标字典 |

每个正式指标对象至少返回：

```json
{
  "value": null,
  "caliber": "已确认或待确认的口径说明",
  "source": "未接入",
  "updated_at": null,
  "conflict": false,
  "unit": "元",
  "status": "待确认"
}
```

缺少事实、映射或口径发布版本时 `value` 必须为 `null`，并返回 `gate.missing_published_versions` 或 `gate.unmapped_facts`；严禁生成演示经营数值。

## 复核与发布

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| GET | `/api/v1/review/items` | `review:view` | 待复核池，支持 `entity_type`、`status` 过滤 |
| POST | `/api/v1/review/discover` | `review:confirm` | 登记系统识别值与 AI/规则建议 |
| POST | `/api/v1/review/confirm` | `review:confirm` | 人工确认并生成草稿；可选直接发布 |
| POST | `/api/v1/review/publish` | `review:publish` | 发布草稿版本 |
| GET | `/api/v1/review/versions` | `review:view` | 查看版本历史 |
| GET | `/api/v1/review/api-cards` | `review:view` | 销售/库存/采购/调拨接口确认卡 |
| GET | `/api/v1/review/audit-log` | `review:view` | 复核与发布审计 |

正式版本命名：`sales_caliber_vX`、`inventory_caliber_vX`、`warehouse_mapping_vX`、`channel_mapping_vX`、`sku_mapping_vX`、`sales_adjustment_rules_vX`。

复核项拆分为 `raw_code`、`raw_name`、`history_mapping`、`suggested_display_name`、`display_name`、`business_unit`、`channel`、`store_shop`、`inventory_class`、`status` 和 `version`。系统可在首次发现时同时提交稳定 `source_key`用于识别同一来源对象；之后 `raw_code`、`raw_name`、`history_mapping` 永久只读。API重复识别或确认请求尝试修改raw字段时返回422。确认请求必须包含 `reason` 和 `affected_metrics`，映射项必须由PO确认 `display_name`。只有确认并发布的展示名和映射规则进入正式维表。

版本及审计记录持久化 `before`、`after`、`reason`、`affected_metrics`、`confirmed_by/at`、`published_by/at`。阈值版本使用 `anomaly_thresholds_vX`。

## 事实写入与追溯

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| POST | `/api/v1/facts/sales/upsert` | `api:inspect` | 通过显式字段映射写入销售事实；不会直接开启正式 KPI |
| POST | `/api/v1/facts/inventory/upsert` | `api:inspect` | 写入库存快照事实；不会直接开启正式 KPI |
| POST | `/api/v1/facts/inventory-aging/upsert` | `api:inspect` | 写入已结构化库龄上传记录；未确认记录不展示正式数值 |
| POST | `/api/v1/actions/upsert` | `review:confirm` | 写入最小动作台账；动作类型和状态使用封闭枚举 |

销售 upsert 键为 `source_system + trade_no + line_id`。同步优先使用 `modified_time` 或等同更新时间；接口不稳定时使用滚动回溯窗口和同一业务键 upsert。`consign_time` 不得用于决定付款销售事实是否入库。

`sales/daily` 读取销售事实、已发布 `sales_caliber`、状态调整及仓库/渠道/SKU映射，支持 `start`、`end`、`channel`。`inventory/aging` 固定输出 `<90`、`90-180`、`180-360`、`360+`，并返回来源、口径、更新时间和确认状态。`anomaly/list` 仅在 `anomaly_thresholds` 已发布且依赖指标可用时形成缺货、高库存、长库龄和慢动销结论；政策数据未接入时政策风险保持“待接入”。

## Sandbox

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| GET | `/api/v1/sandbox/compare` | `sandbox:view` | 快照文件身份/结构与正式门禁对照 |
| POST | `/api/v1/sandbox/compare` | `sandbox:view` | 销售或库存旧/新记录差异比较 |
| POST | `/api/v1/sandbox/recompute-times` | `sandbox:view` | 五时间字段口径复算，不写正式指标 |

所有 Sandbox 响应包含 `mode: sandbox`、`验证数据，不代表正式经营口径` 和 `formal_kpi_enabled: false` 或等价隔离说明。

## Demo Adapter

只有进程环境 `DEMO_MODE=true` 时才会创建纯 Mock Demo Adapter。Demo 业务响应必须包含：

- `mode: demo`；
- `data_class: DEMO`；
- `label: 演示数据，仅用于页面及流程验证`；
- `formal_kpi_enabled: false`；
- `real_system_connected: false`。

Demo 模式禁止向正式销售、库存、库龄、动作和复核发现表写入数据；演示复核确认/发布只保存在当前进程内存。`DEMO_MODE=false` 不会在事实或版本缺失时自动回退到 Demo。
