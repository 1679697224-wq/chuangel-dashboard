"""销售/库存事实同步：同步范围与经营统计口径严格分离。"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional


SALES_FACT_FIELDS = (
    "trade_no",
    "line_id",
    "create_time",
    "pay_time",
    "audit_time",
    "consign_time",
    "complete_time",
    "modified_time",
    "trade_status",
    "quantity",
    "payment",
    "warehouse_raw_name",
    "channel_raw_name",
    "store_raw_name",
    "goods_no",
    "sku_raw",
    "source_api",
    "raw_json_reference",
)

SYNC_LABEL = "同步范围只决定事实是否入库；pay_time 等经营主时间由已发布口径版本决定"


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def plan_sales_sync(
    last_modified: Optional[str],
    now: Optional[datetime] = None,
    supports_modified: bool = True,
    lookback_days: int = 7,
) -> Dict[str, Any]:
    """优先按更新时间增量；不支持时使用滚动回溯并按事实业务键 upsert。"""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    if supports_modified:
        return {
            "strategy": "MODIFIED_INCREMENTAL",
            "cursor_field": "modified_time",
            "from": last_modified,
            "to": current.isoformat(),
            "upsert_key": ["source_system", "trade_no", "line_id"],
            "business_time_filter": None,
            "note": SYNC_LABEL,
        }
    if lookback_days < 1:
        raise ValueError("滚动回溯天数必须大于等于 1")
    return {
        "strategy": "ROLLING_LOOKBACK_UPSERT",
        "cursor_field": "modified_time_or_equivalent",
        "from": (current - timedelta(days=lookback_days)).isoformat(),
        "to": current.isoformat(),
        "lookback_days": lookback_days,
        "upsert_key": ["source_system", "trade_no", "line_id"],
        "business_time_filter": None,
        "note": SYNC_LABEL,
    }


def canonical_sales_fact(
    raw: Mapping[str, Any],
    field_mapping: Mapping[str, str],
    metadata: Mapping[str, Any],
) -> Dict[str, Any]:
    """用已复核字段映射生成事实；本函数不按付款/发货时间过滤记录。"""
    record = {
        field: raw.get(field_mapping.get(field, field))
        for field in SALES_FACT_FIELDS
    }
    for key in ("source_system", "source_record_id", "extracted_at", "synced_at", "sync_job_id"):
        source_value = raw.get(field_mapping.get(key, key))
        record[key] = source_value if source_value not in (None, "") else metadata.get(key)
    required = (
        "source_system", "source_record_id", "trade_no", "line_id", "trade_status",
        "warehouse_raw_name", "channel_raw_name", "goods_no", "sku_raw", "source_api",
        "raw_json_reference", "extracted_at", "synced_at", "sync_job_id",
    )
    missing = [field for field in required if record.get(field) in (None, "")]
    if missing:
        raise ValueError("销售事实缺少字段：{}".format(", ".join(missing)))
    reference = record.get("raw_json_reference")
    if not isinstance(reference, str) or reference.lstrip().startswith(("{", "[")):
        raise ValueError("raw_json_reference 必须是受控原始载荷引用，禁止直接写入原始 JSON")
    record["quantity"] = _number(record.get("quantity"))
    record["payment"] = _number(record.get("payment"))
    record["store_raw_name"] = record.get("store_raw_name") or ""
    return record


def canonical_inventory_fact(
    raw: Mapping[str, Any],
    field_mapping: Mapping[str, str],
    metadata: Mapping[str, Any],
) -> Dict[str, Any]:
    fields = (
        "snapshot_time", "warehouse_raw_name", "sku_raw", "quantity", "amount",
        "source_api", "raw_json_reference",
    )
    record = {field: raw.get(field_mapping.get(field, field)) for field in fields}
    for key in ("source_system", "source_record_id", "extracted_at", "synced_at", "sync_job_id"):
        source_value = raw.get(field_mapping.get(key, key))
        record[key] = source_value if source_value not in (None, "") else metadata.get(key)
    required = tuple(field for field in record if field not in {"quantity", "amount"})
    missing = [field for field in required if record.get(field) in (None, "")]
    if missing:
        raise ValueError("库存事实缺少字段：{}".format(", ".join(missing)))
    reference = record.get("raw_json_reference")
    if not isinstance(reference, str) or reference.lstrip().startswith(("{", "[")):
        raise ValueError("raw_json_reference 必须是受控原始载荷引用，禁止直接写入原始 JSON")
    record["quantity"] = _number(record.get("quantity"))
    record["amount"] = _number(record.get("amount"))
    return record


def build_status_review(
    records: Iterable[Mapping[str, Any]],
    current_rules: Optional[Mapping[str, str]] = None,
) -> List[Dict[str, Any]]:
    """聚合源状态；程序仅给建议，不代替 PO 确认。"""
    buckets: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"orders": set(), "amount": 0.0}
    )
    for record in records:
        status = str(record.get("trade_status") or "<空状态>").strip()
        bucket = buckets[status]
        bucket["orders"].add(str(record.get("trade_no") or ""))
        bucket["amount"] += _number(record.get("payment"))
    rules = current_rules or {}
    result = []
    for status in sorted(buckets):
        text = status.lower()
        suggestion = "PENDING"
        if any(word in text for word in ("取消", "关闭", "cancel", "closed")):
            suggestion = "建议排除，待 PO 确认"
        elif any(word in text for word in ("退款", "退货", "红冲", "refund", "return")):
            suggestion = "建议进入调整规则复核，待 PO 确认"
        elif any(word in text for word in ("付款", "完成", "发货", "paid", "complete", "consign")):
            suggestion = "建议复核是否计销售，待 PO 确认"
        current = rules.get(status, "未发布规则")
        result.append(
            {
                "raw_trade_status": status,
                "order_count": len(buckets[status]["orders"] - {""}),
                "sales_amount": round(buckets[status]["amount"], 2),
                "current_rule": current,
                "program_suggestion": suggestion,
                "count_as_sales": None,
                "count_as_pending_audit": None,
                "offset_sales": None,
                "exclude": None,
                "human_confirmation_status": "待PO确认",
            }
        )
    return result
