# 采销经营驾驶舱 API V1

基础路径：`/api/v1/`。除健康检查和登录外，接口必须使用 HttpOnly 会话 Cookie 或 `Authorization: Bearer <token>` 鉴权。

## 正式接口

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| GET | `/api/v1/health` | 公开 | 存活检查，不返回环境详情或凭据 |
| POST | `/api/v1/auth/login` | 公开 | 登录，5 次失败后临时阻断 |
| POST | `/api/v1/auth/logout` | 已登录 | 撤销服务端会话 |
| GET | `/api/v1/auth/me` | `dashboard:view` | 当前账号、功能权限和数据范围 |
| GET | `/api/v1/dim/boards` | `dashboard:view` | 看板模块 |
| GET | `/api/v1/dim/channels` | `dashboard:view` | 仅已发布渠道映射 |
| GET | `/api/v1/dim/warehouses` | `dashboard:view` | 仅已发布仓库映射 |
| GET | `/api/v1/dim/skus` | `dashboard:view` | 仅已发布 SKU 映射 |
| GET | `/api/v1/sales/summary` | `dashboard:view` | 销售核心指标 |
| GET | `/api/v1/sales/daily` | `dashboard:view` | 销售日趋势 |
| GET | `/api/v1/sales/sku/{sku}` | `dashboard:view` | SKU 销售视图 |
| GET | `/api/v1/inventory/summary` | `dashboard:view` | 三库存视图总览 |
| GET | `/api/v1/inventory/aging` | `dashboard:view` | 库龄明细 |
| GET | `/api/v1/purchase/summary` | `dashboard:view` | 采购与在途 |
| GET | `/api/v1/policy/summary` | `dashboard:view` | Apple 政策经营 |
| GET | `/api/v1/anomaly/list` | `dashboard:view` | 经营异常 |
| GET | `/api/v1/action/list` | `dashboard:view` | 待确认经营动作 |
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
  "status": "待接入"
}
```

没有真实数据时 `value` 必须为 `null`，严禁生成演示经营数值。

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

正式版本命名：`sales_caliber_vX`、`inventory_caliber_vX`、`warehouse_mapping_vX`、`channel_mapping_vX`、`sku_mapping_vX`。

## Sandbox

| 方法 | 路径 | 权限 | 用途 |
|---|---|---|---|
| GET | `/api/v1/sandbox/compare` | `sandbox:view` | 快照文件身份/结构与正式门禁对照 |
| POST | `/api/v1/sandbox/recompute-times` | `sandbox:view` | 五时间字段口径复算，不写正式指标 |

所有 Sandbox 响应包含 `mode: sandbox` 和 `formal_kpi_enabled: false` 或等价隔离说明。
