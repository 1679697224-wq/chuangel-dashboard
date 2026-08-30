"""Sandbox 差异引擎。输出永远不能成为正式经营 KPI。"""

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping


SANDBOX_LABEL = "验证数据，不代表正式经营口径"


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _group(records: Iterable[Mapping[str, Any]], field: str, amount_field: str) -> Dict[str, float]:
    result: Dict[str, float] = defaultdict(float)
    for record in records:
        fallback = "payment" if amount_field == "amount" else "amount"
        result[str(record.get(field) or "<空>")] += _number(record.get(amount_field, record.get(fallback)))
    return {key: round(value, 2) for key, value in sorted(result.items())}


def _group_diff(
    old_records: List[Mapping[str, Any]],
    new_records: List[Mapping[str, Any]],
    field: str,
    old_amount: str,
    new_amount: str,
) -> List[Dict[str, Any]]:
    old = _group(old_records, field, old_amount)
    new = _group(new_records, field, new_amount)
    return [
        {"key": key, "old": old.get(key, 0.0), "new": new.get(key, 0.0), "difference": round(new.get(key, 0.0) - old.get(key, 0.0), 2)}
        for key in sorted(set(old) | set(new))
        if round(new.get(key, 0.0) - old.get(key, 0.0), 2) != 0
    ]


def compare_sales(
    old_records: Iterable[Mapping[str, Any]],
    new_records: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    old_rows, new_rows = list(old_records), list(new_records)
    old_orders: Dict[str, float] = defaultdict(float)
    new_orders: Dict[str, float] = defaultdict(float)
    for row in old_rows:
        old_orders[str(row.get("trade_no") or "")] += _number(row.get("amount", row.get("payment")))
    for row in new_rows:
        if row.get("pay_time"):
            new_orders[str(row.get("trade_no") or "")] += _number(row.get("payment", row.get("amount")))
    old_orders.pop("", None)
    new_orders.pop("", None)
    only_old = sorted(set(old_orders) - set(new_orders))
    only_new = sorted(set(new_orders) - set(old_orders))
    mismatch = sorted(
        key for key in set(old_orders) & set(new_orders)
        if round(old_orders[key] - new_orders[key], 2) != 0
    )
    old_total = round(sum(old_orders.values()), 2)
    new_total = round(sum(new_orders.values()), 2)
    difference = round(new_total - old_total, 2)
    return {
        "mode": "sandbox",
        "label": SANDBOX_LABEL,
        "domain": "sales",
        "old_sales_amount": old_total,
        "new_sales_amount_by_pay_time": new_total,
        "difference": difference,
        "difference_rate": None if old_total == 0 else round(difference / old_total, 6),
        "different_order_count": len(set(only_old) | set(only_new) | set(mismatch)),
        "only_old_orders": only_old,
        "only_new_orders": only_new,
        "amount_mismatch_orders": [
            {"trade_no": key, "old": round(old_orders[key], 2), "new": round(new_orders[key], 2), "difference": round(new_orders[key] - old_orders[key], 2)}
            for key in mismatch
        ],
        "channel_differences": _group_diff(old_rows, new_rows, "channel_raw_name", "amount", "payment"),
        "store_differences": _group_diff(old_rows, new_rows, "store_raw_name", "amount", "payment"),
        "sku_differences": _group_diff(old_rows, new_rows, "sku_raw", "amount", "payment"),
        "formal_kpi_enabled": False,
    }


def compare_inventory(
    old_records: Iterable[Mapping[str, Any]],
    new_records: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    old_rows, new_rows = list(old_records), list(new_records)
    old_qty = round(sum(_number(row.get("quantity")) for row in old_rows), 4)
    new_qty = round(sum(_number(row.get("quantity")) for row in new_rows), 4)
    old_amount = round(sum(_number(row.get("amount")) for row in old_rows), 2)
    new_amount = round(sum(_number(row.get("amount")) for row in new_rows), 2)
    old_pairs = {(str(row.get("warehouse_raw_name")), str(row.get("sku_raw"))) for row in old_rows}
    new_pairs = {(str(row.get("warehouse_raw_name")), str(row.get("sku_raw"))) for row in new_rows}
    old_mapping = {
        (str(row.get("warehouse_raw_name")), str(row.get("sku_raw"))):
        (row.get("warehouse_mapped"), row.get("sku_mapped"), row.get("inventory_class"))
        for row in old_rows
    }
    new_mapping = {
        (str(row.get("warehouse_raw_name")), str(row.get("sku_raw"))):
        (row.get("warehouse_mapped"), row.get("sku_mapped"), row.get("inventory_class"))
        for row in new_rows
    }
    changed_mapping = [
        {"warehouse_raw_name": key[0], "sku_raw": key[1], "old_mapping": old_mapping[key], "new_mapping": new_mapping[key]}
        for key in sorted(set(old_mapping) & set(new_mapping))
        if old_mapping[key] != new_mapping[key]
    ]
    return {
        "mode": "sandbox",
        "label": SANDBOX_LABEL,
        "domain": "inventory",
        "quantity": {"old": old_qty, "new": new_qty, "difference": round(new_qty - old_qty, 4)},
        "amount": {"old": old_amount, "new": new_amount, "difference": round(new_amount - old_amount, 2)},
        "warehouse_differences": _group_diff(old_rows, new_rows, "warehouse_raw_name", "quantity", "quantity"),
        "sku_differences": _group_diff(old_rows, new_rows, "sku_raw", "quantity", "quantity"),
        "mapping_differences": {
            "only_old": sorted([{"warehouse_raw_name": a, "sku_raw": b} for a, b in old_pairs - new_pairs], key=lambda item: (item["warehouse_raw_name"], item["sku_raw"])),
            "only_new": sorted([{"warehouse_raw_name": a, "sku_raw": b} for a, b in new_pairs - old_pairs], key=lambda item: (item["warehouse_raw_name"], item["sku_raw"])),
            "changed": changed_mapping,
        },
        "formal_kpi_enabled": False,
    }
