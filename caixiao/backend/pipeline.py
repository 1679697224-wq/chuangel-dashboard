"""吉客云原始数据到指标层的可追溯转换骨架。"""

from datetime import datetime
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional


SALES_TIME_FIELDS = (
    "create_time",
    "pay_time",
    "audit_time",
    "consign_time",
    "complete_time",
)


def _stable_trace_id(
    domain: str, source_system: str, source_record_id: str, extracted_at: str
) -> str:
    material = "|".join((domain, source_system, source_record_id, extracted_at))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def clean_sales_record(
    raw: Mapping[str, Any], field_mapping: Mapping[str, str]
) -> Dict[str, Any]:
    """按人工确认的字段映射清洗；五个时间字段始终独立保留。"""
    cleaned: Dict[str, Any] = {}
    for canonical, source_field in field_mapping.items():
        cleaned[canonical] = raw.get(source_field)
    for field in SALES_TIME_FIELDS:
        cleaned.setdefault(field, raw.get(field))
    return cleaned


def build_sales_trace(
    raw: Mapping[str, Any],
    source_record_id: str,
    extracted_at: str,
    field_mapping: Mapping[str, str],
    dimension_mapping: Mapping[str, Mapping[str, Any]],
    mapping_version: Optional[str],
) -> Dict[str, Any]:
    cleaned = clean_sales_record(raw, field_mapping)
    mapped = dict(cleaned)
    mapping_state = "CONFIRMED" if mapping_version else "UNCONFIRMED"
    for field, mapping in dimension_mapping.items():
        original = cleaned.get(field)
        mapped[field] = mapping.get(str(original), original)
    return {
        "trace_id": _stable_trace_id("sales", "jikexyun", source_record_id, extracted_at),
        "domain": "sales",
        "source_system": "jikexyun",
        "source_record_id": source_record_id,
        "raw": dict(raw),
        "cleaned": cleaned,
        "mapped": mapped,
        "mapping_version": mapping_version,
        "mapping_state": mapping_state,
        "eligible_for_formal_kpi": bool(mapping_version),
        "extracted_at": extracted_at,
    }


def sales_amount_by_time(
    records: Iterable[Mapping[str, Any]], time_field: str, amount_field: str
) -> Dict[str, float]:
    """用于 Sandbox 复算五时间口径；不自行选择正式主时间。"""
    if time_field not in SALES_TIME_FIELDS:
        raise ValueError("不支持的销售时间字段")
    totals: Dict[str, float] = {}
    for record in records:
        raw_time = record.get(time_field)
        if not raw_time:
            continue
        date_key = str(raw_time)[:10]
        try:
            amount = float(record.get(amount_field) or 0)
        except (TypeError, ValueError):
            amount = 0.0
        totals[date_key] = round(totals.get(date_key, 0.0) + amount, 2)
    return totals


def recompute_five_time_views(
    records: Iterable[Mapping[str, Any]], amount_field: str
) -> Dict[str, Dict[str, float]]:
    materialized: List[Mapping[str, Any]] = list(records)
    return {
        field: sales_amount_by_time(materialized, field, amount_field)
        for field in SALES_TIME_FIELDS
    }


def inventory_relationship_check(
    quantity: Any, locked: Any, available: Any, tolerance: float = 0.0001
) -> Dict[str, Any]:
    try:
        quantity_number = float(quantity)
        locked_number = float(locked)
        available_number = float(available)
    except (TypeError, ValueError):
        return {"valid": False, "reason": "NON_NUMERIC", "difference": None}
    difference = round(quantity_number - locked_number - available_number, 6)
    return {
        "valid": abs(difference) <= tolerance,
        "reason": "OK" if abs(difference) <= tolerance else "RELATION_MISMATCH",
        "difference": difference,
    }


def serialize_trace(trace: Mapping[str, Any]) -> str:
    return json.dumps(trace, ensure_ascii=False, sort_keys=True, default=str)


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
