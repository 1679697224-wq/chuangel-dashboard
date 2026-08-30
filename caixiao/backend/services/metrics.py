"""正式经营指标：事实、映射、口径和发布版本共同通过后才计算。"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from ..database import Database
from ..models import AdjustmentAction, InventoryClass
from .review import ReviewService


METRIC_DICTIONARY = [
    {"code": "sales_amount", "name": "销售额", "caliber": "由已发布 sales_caliber 指定主时间；状态调整由已发布 sales_adjustment_rules 决定", "source": "吉客云事实层", "unit": "元", "required_versions": ["sales_caliber", "sales_adjustment_rules", "warehouse_mapping", "channel_mapping", "sku_mapping"]},
    {"code": "paid_orders", "name": "订单数", "caliber": "按已发布销售口径时间过滤并按 trade_no 去重", "source": "吉客云事实层", "unit": "单", "required_versions": ["sales_caliber", "sales_adjustment_rules", "warehouse_mapping", "channel_mapping", "sku_mapping"]},
    {"code": "spot_inventory_qty", "name": "现货库存", "caliber": "已发布仓库映射归类为 SPOT 的库存", "source": "吉客云库存事实层", "unit": "台", "required_versions": ["inventory_caliber", "warehouse_mapping", "sku_mapping"]},
    {"code": "in_transit_inventory_qty", "name": "在途库存", "caliber": "已发布仓库映射及 inventory_caliber 归类为 IN_TRANSIT 的库存", "source": "吉客云库存事实层", "unit": "台", "required_versions": ["inventory_caliber", "warehouse_mapping", "sku_mapping"]},
    {"code": "operating_inventory_qty", "name": "经营库存", "caliber": "现货库存 + 符合已发布经营规则的在途库存", "source": "吉客云库存事实层", "unit": "台", "required_versions": ["inventory_caliber", "warehouse_mapping", "sku_mapping"]},
    {"code": "inventory_value", "name": "经营库存金额", "caliber": "现货及符合规则的在途金额；成本字段仍需 PO 确认", "source": "吉客云库存事实层", "unit": "元", "required_versions": ["inventory_caliber", "warehouse_mapping", "sku_mapping"]},
    {"code": "spot_woi", "name": "现货WOI", "caliber": "现货 ÷（配置窗口销量/窗口天数×7）", "source": "销售与库存事实层", "unit": "周", "required_versions": ["sales_caliber", "sales_adjustment_rules", "inventory_caliber", "warehouse_mapping", "channel_mapping", "sku_mapping"]},
    {"code": "operating_woi", "name": "含在途WOI", "caliber": "经营库存 ÷（配置窗口销量/窗口天数×7）", "source": "销售与库存事实层", "unit": "周", "required_versions": ["sales_caliber", "sales_adjustment_rules", "inventory_caliber", "warehouse_mapping", "channel_mapping", "sku_mapping"]},
    {"code": "purchase_open_qty", "name": "在途采购量", "caliber": "采购/调拨正式事实接入及口径发布后展示", "source": "吉客云 API（待联调）", "unit": "台", "required_versions": ["inventory_caliber", "warehouse_mapping", "sku_mapping"]},
]


def _version_map(version: Optional[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not version:
        return {}
    result: Dict[str, Dict[str, Any]] = {}
    for entry in version.get("payload", []):
        value = entry.get("value")
        result[str(entry.get("source_key"))] = value if isinstance(value, dict) else {}
    return result


def _parse_time(value: Any) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def calculate_dual_woi(
    spot_inventory: float,
    in_transit_inventory: float,
    sales_quantity: float,
    window_days: int = 28,
) -> Dict[str, Any]:
    """计算双 WOI，并显式处理全部零销量/零库存场景。"""
    if window_days < 1:
        raise ValueError("销量窗口天数必须大于等于 1")
    operating = spot_inventory + in_transit_inventory
    if sales_quantity == 0:
        if operating == 0:
            return {"spot": None, "operating": None, "state": "NO_INVENTORY_NO_SALES", "window_days": window_days}
        return {"spot": None, "operating": None, "state": "INVENTORY_WITHOUT_SALES", "window_days": window_days}
    weekly_sales = sales_quantity / window_days * 7
    if operating == 0:
        return {"spot": 0.0, "operating": 0.0, "state": "SALES_WITHOUT_INVENTORY", "window_days": window_days}
    return {
        "spot": round(spot_inventory / weekly_sales, 4),
        "operating": round(operating / weekly_sales, 4),
        "state": "CALCULATED",
        "window_days": window_days,
    }


class MetricsService:
    def __init__(self, review_service: ReviewService, database: Database):
        self.review = review_service
        self.database = database

    @staticmethod
    def dictionary() -> List[Dict[str, Any]]:
        return METRIC_DICTIONARY

    @staticmethod
    def _metric(definition: Mapping[str, Any], value: Any, status: str, updated_at: Optional[str], detail: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result = {
            "code": definition["code"], "name": definition["name"], "value": value,
            "caliber": definition["caliber"], "source": definition["source"],
            "updated_at": updated_at, "conflict": False, "unit": definition["unit"],
            "status": status,
        }
        if detail:
            result["detail"] = detail
        return result

    def _definitions(self, codes: Iterable[str]) -> List[Dict[str, Any]]:
        indexed = {item["code"]: item for item in METRIC_DICTIONARY}
        return [indexed[code] for code in codes if code in indexed]

    def _gate(self, definitions: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
        required = sorted({version for item in definitions for version in item["required_versions"]})
        missing = [name for name in required if not self.database.published_version(name)]
        return {
            "eligible": not missing,
            "required_versions": required,
            "missing_published_versions": missing,
            "gate": "事实数据 → 已发布映射版本 → 已发布口径版本 → 正式 KPI",
        }

    def _pending(self, definitions: Iterable[Mapping[str, Any]], gate: Mapping[str, Any], reason: str = "缺少已发布版本") -> Dict[str, Any]:
        return {
            "mode": "formal",
            "data": [self._metric(item, None, "待确认", None, {"reason": reason, "missing_versions": gate.get("missing_published_versions", [])}) for item in definitions],
            "gate": dict(gate),
            "message": "待确认",
            "generated_business_data": False,
        }

    def _mappings(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return {
            name: _version_map(self.database.published_version(name))
            for name in ("warehouse_mapping", "channel_mapping", "sku_mapping", "sales_adjustment_rules")
        }

    def _sales_context(self, records: List[Mapping[str, Any]]) -> Tuple[List[Mapping[str, Any]], Dict[str, Any]]:
        mappings = self._mappings()
        caliber_entries = _version_map(self.database.published_version("sales_caliber"))
        caliber = caliber_entries.get("default") or next(iter(caliber_entries.values()), {})
        time_field = str(caliber.get("time_field") or "")
        if time_field not in {"create_time", "pay_time", "audit_time", "consign_time", "complete_time"}:
            return [], {"reason": "sales_caliber 未配置有效 time_field", "unmapped": []}
        unmapped = []
        included = []
        for record in records:
            missing = []
            warehouse = mappings["warehouse_mapping"].get(str(record.get("warehouse_raw_name")))
            channel = mappings["channel_mapping"].get(str(record.get("channel_raw_name")))
            sku = mappings["sku_mapping"].get(str(record.get("sku_raw")))
            adjustment = mappings["sales_adjustment_rules"].get(str(record.get("trade_status")))
            if not warehouse or not warehouse.get("canonical"):
                missing.append("warehouse_mapping:{}".format(record.get("warehouse_raw_name")))
            if not channel or not channel.get("canonical"):
                missing.append("channel_mapping:{}".format(record.get("channel_raw_name")))
            if not sku or not sku.get("canonical"):
                missing.append("sku_mapping:{}".format(record.get("sku_raw")))
            if not adjustment:
                missing.append("sales_adjustment_rules:{}".format(record.get("trade_status")))
            action = str((adjustment or {}).get("action", "PENDING"))
            if action not in {item.value for item in AdjustmentAction}:
                missing.append("sales_adjustment_rules:{}动作无效".format(record.get("trade_status")))
            if action == AdjustmentAction.PENDING.value:
                missing.append("sales_adjustment_rules:{}=PENDING".format(record.get("trade_status")))
            if action == AdjustmentAction.OFFSET.value and not isinstance((adjustment or {}).get("multiplier"), (int, float)):
                missing.append("sales_adjustment_rules:{}缺少multiplier".format(record.get("trade_status")))
            if missing:
                unmapped.extend(missing)
                continue
            if action == AdjustmentAction.EXCLUDE.value:
                continue
            copy = dict(record)
            copy["metric_time"] = record.get(time_field)
            copy["canonical_warehouse"] = warehouse.get("canonical")
            copy["canonical_channel"] = channel.get("canonical")
            copy["canonical_sku"] = sku.get("canonical")
            copy["business_unit"] = channel.get("business_unit") or ""
            copy["brand"] = sku.get("brand") or ""
            multiplier = float(adjustment.get("multiplier", 1))
            copy["metric_payment"] = float(record.get("payment") or 0) * multiplier
            copy["metric_quantity"] = float(record.get("quantity") or 0) * multiplier
            included.append(copy)
        return included, {"reason": "" if not unmapped else "存在未映射或未裁定事实", "unmapped": sorted(set(unmapped)), "time_field": time_field}

    def sales_summary(self, sku: str = "", filters: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
        definitions = self._definitions(("sales_amount", "paid_orders"))
        gate = self._gate(definitions)
        requested = dict(filters or {})
        unsupported = []
        if requested.get("compare") not in (None, "", "none"):
            unsupported.append("compare")
        if unsupported:
            gate.update({"eligible": False, "pending_filter_fields": unsupported})
            return self._pending(definitions, gate, "筛选字段尚未进入事实合同")
        if not gate["eligible"]:
            return self._pending(definitions, gate)
        records = self.database.list_sales_facts(sku)
        if not records:
            gate["eligible"] = False
            return self._pending(definitions, gate, "销售事实尚未接入")
        included, context = self._sales_context(records)
        if context["unmapped"] or context["reason"]:
            gate.update({"eligible": False, "unmapped_facts": context["unmapped"]})
            return self._pending(definitions, gate, context["reason"])
        if requested.get("channel"):
            included = [record for record in included if requested["channel"] in {str(record.get("channel_raw_name")), str(record.get("canonical_channel"))}]
        for field in ("business_unit", "brand"):
            if requested.get(field):
                if any(not record.get(field) for record in included):
                    gate.update({"eligible": False, "pending_filter_fields": [field]})
                    return self._pending(definitions, gate, "筛选字段尚未完成已发布映射")
                included = [record for record in included if str(record.get(field)) == requested[field]]
        start = _parse_time(requested.get("start"))
        end = _parse_time(requested.get("end"))
        dated = []
        for record in included:
            metric_time = _parse_time(record.get("metric_time"))
            if not metric_time or (start and metric_time < start) or (end and metric_time >= end + timedelta(days=1)):
                continue
            dated.append(record)
        updated_at = max((str(record.get("synced_at") or "") for record in records), default=None)
        data = [
            self._metric(definitions[0], round(sum(record["metric_payment"] for record in dated), 2), "正式", updated_at),
            self._metric(definitions[1], len({record["trade_no"] for record in dated}), "正式", updated_at),
        ]
        return {"mode": "formal", "data": data, "gate": gate, "message": "已按发布版本计算", "generated_business_data": False, "source_record_count": len(records), "sales_time_field": context["time_field"], "filters_applied": requested}

    def sales_daily(self, filters: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
        definitions = self._definitions(("sales_amount", "paid_orders"))
        gate = self._gate(definitions)
        requested = dict(filters or {})
        if requested.get("compare") not in (None, "", "none"):
            gate.update({"eligible": False, "pending_filter_fields": ["compare"]})
            return {**self._pending(definitions, gate, "对比趋势口径尚未发布"), "rows": []}
        if not gate["eligible"]:
            return {**self._pending(definitions, gate), "rows": []}
        records = self.database.list_sales_facts()
        if not records:
            gate["eligible"] = False
            return {**self._pending(definitions, gate, "销售事实尚未接入"), "rows": []}
        included, context = self._sales_context(records)
        if context["unmapped"] or context["reason"]:
            gate.update({"eligible": False, "unmapped_facts": context["unmapped"]})
            return {**self._pending(definitions, gate, context["reason"]), "rows": []}
        if requested.get("channel"):
            included = [record for record in included if requested["channel"] in {str(record.get("channel_raw_name")), str(record.get("canonical_channel"))}]
        for field in ("business_unit", "brand"):
            if requested.get(field):
                if any(not record.get(field) for record in included):
                    gate.update({"eligible": False, "pending_filter_fields": [field]})
                    return {**self._pending(definitions, gate, "筛选字段尚未完成已发布映射"), "rows": []}
                included = [record for record in included if str(record.get(field)) == requested[field]]
        start = _parse_time(requested.get("start"))
        end = _parse_time(requested.get("end"))
        buckets: Dict[str, Dict[str, Any]] = {}
        for record in included:
            metric_time = _parse_time(record.get("metric_time"))
            if not metric_time or (start and metric_time < start) or (end and metric_time >= end + timedelta(days=1)):
                continue
            day = metric_time.date().isoformat()
            bucket = buckets.setdefault(day, {"sales_amount": 0.0, "orders": set()})
            bucket["sales_amount"] += float(record["metric_payment"])
            bucket["orders"].add(str(record["trade_no"]))
        updated_at = max((str(record.get("synced_at") or "") for record in records), default=None)
        rows = [
            {
                "date": day,
                "sales_amount": round(bucket["sales_amount"], 2),
                "order_count": len(bucket["orders"]),
                "source": "吉客云销售事实层",
                "caliber": context["time_field"],
                "updated_at": updated_at,
                "status": "正式",
            }
            for day, bucket in sorted(buckets.items())
        ]
        return {
            "mode": "formal", "rows": rows, "gate": gate,
            "message": "已按发布版本计算" if rows else "待接入",
            "generated_business_data": False, "sales_time_field": context["time_field"],
            "filters_applied": requested, "source_record_count": len(records),
        }

    def inventory_aging(self) -> Dict[str, Any]:
        bucket_specs = (("<90", 0, 89), ("90-180", 90, 179), ("180-360", 180, 359), ("360+", 360, None))
        empty_rows = [
            {"bucket": label, "quantity": None, "amount": None, "status": "待接入"}
            for label, _, _ in bucket_specs
        ]
        required = ("inventory_caliber", "warehouse_mapping", "sku_mapping")
        missing = [name for name in required if not self.database.published_version(name)]
        gate = {"eligible": not missing, "required_versions": list(required), "missing_published_versions": missing}
        records = self.database.list_inventory_aging_records()
        if not records:
            return {"mode": "formal", "rows": empty_rows, "gate": gate, "message": "待接入", "source": None, "caliber": None, "updated_at": None, "confirmation_status": "待接入", "generated_business_data": False}
        if missing or any(record["confirmation_status"] != "CONFIRMED" for record in records):
            gate["eligible"] = False
            return {"mode": "formal", "rows": [{**row, "status": "待确认"} for row in empty_rows], "gate": gate, "message": "待确认", "source": sorted({record["source_system"] for record in records}), "caliber": sorted({record["caliber"] for record in records}), "updated_at": max(record["synced_at"] for record in records), "confirmation_status": "待确认", "generated_business_data": False}
        warehouse_map = _version_map(self.database.published_version("warehouse_mapping"))
        sku_map = _version_map(self.database.published_version("sku_mapping"))
        unmapped = [
            record["source_record_id"] for record in records
            if not warehouse_map.get(record["warehouse_raw_name"], {}).get("canonical")
            or not sku_map.get(record["sku_raw"], {}).get("canonical")
        ]
        if unmapped:
            gate.update({"eligible": False, "unmapped_records": sorted(set(unmapped))})
            return {"mode": "formal", "rows": [{**row, "status": "待确认"} for row in empty_rows], "gate": gate, "message": "存在未发布仓库或SKU映射", "source": sorted({record["source_system"] for record in records}), "caliber": sorted({record["caliber"] for record in records}), "updated_at": max(record["synced_at"] for record in records), "confirmation_status": "待确认", "generated_business_data": False}
        rows = []
        for label, minimum, maximum in bucket_specs:
            selected = [record for record in records if record["age_days"] >= minimum and (maximum is None or record["age_days"] <= maximum)]
            rows.append({"bucket": label, "quantity": round(sum(record["quantity"] for record in selected), 4), "amount": round(sum(record["amount"] for record in selected), 2), "status": "正式"})
        return {"mode": "formal", "rows": rows, "gate": gate, "message": "已按确认上传数据和发布映射计算", "source": sorted({record["source_system"] for record in records}), "caliber": sorted({record["caliber"] for record in records}), "updated_at": max(record["synced_at"] for record in records), "confirmation_status": "已确认", "generated_business_data": False}

    def anomaly_list(self) -> Dict[str, Any]:
        names = ("缺货", "高库存", "长库龄", "慢动销", "政策风险")
        pending = [{"type": name, "status": "待确认", "conclusion": None} for name in names]
        threshold_version = self.database.published_version("anomaly_thresholds")
        thresholds = _version_map(threshold_version).get("default") if threshold_version else None
        required = ("stockout_qty_max", "high_inventory_qty_min", "long_aging_amount_min", "slow_moving_woi_min")
        if not thresholds or any(not isinstance(thresholds.get(key), (int, float)) for key in required):
            return {"data": pending, "message": "异常阈值待确认并发布", "threshold_version": None, "generated_business_data": False}
        inventory = self.inventory_summary()
        aging = self.inventory_aging()
        woi = self.woi_summary()
        inv_values = {item["code"]: item["value"] for item in inventory.get("data", [])}
        woi_values = {item["code"]: item["value"] for item in woi.get("data", [])}
        aging_360 = next((item for item in aging.get("rows", []) if item["bucket"] == "360+"), {})
        def conclusion(ready: bool, triggered: bool) -> Dict[str, Any]:
            return {"status": "异常" if triggered else "正常", "conclusion": triggered} if ready else {"status": "待确认", "conclusion": None}
        stock = conclusion(inventory.get("gate", {}).get("eligible", False), (inv_values.get("operating_inventory_qty") or 0) <= thresholds["stockout_qty_max"])
        high = conclusion(inventory.get("gate", {}).get("eligible", False), (inv_values.get("operating_inventory_qty") or 0) >= thresholds["high_inventory_qty_min"])
        long_age = conclusion(aging.get("gate", {}).get("eligible", False), (aging_360.get("amount") or 0) >= thresholds["long_aging_amount_min"])
        slow = conclusion(woi.get("gate", {}).get("eligible", False) and woi_values.get("operating_woi") is not None, (woi_values.get("operating_woi") or 0) >= thresholds["slow_moving_woi_min"])
        data = [
            {"type": "缺货", **stock}, {"type": "高库存", **high},
            {"type": "长库龄", **long_age}, {"type": "慢动销", **slow},
            {"type": "政策风险", "status": "待接入", "conclusion": None},
        ]
        return {"data": data, "message": "仅已发布阈值可形成结论", "threshold_version": threshold_version["version_name"], "generated_business_data": False}

    def inventory_summary(self, sku: str = "", filters: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
        definitions = self._definitions(("spot_inventory_qty", "in_transit_inventory_qty", "operating_inventory_qty", "inventory_value"))
        gate = self._gate(definitions)
        requested = {key: value for key, value in dict(filters or {}).items() if value not in (None, "", "none")}
        if requested:
            gate.update({"eligible": False, "pending_filter_fields": sorted(requested)})
            return self._pending(definitions, gate, "库存事实尚未具备所选全局筛选字段/期间对比合同")
        if not gate["eligible"]:
            return self._pending(definitions, gate)
        warehouse_map = _version_map(self.database.published_version("warehouse_mapping"))
        sku_map = _version_map(self.database.published_version("sku_mapping"))
        inventory_entries = _version_map(self.database.published_version("inventory_caliber"))
        inventory_caliber = inventory_entries.get("default") or next(iter(inventory_entries.values()), {})
        operating_classes = inventory_caliber.get("operating_classes")
        valid_inventory_classes = {item.value for item in InventoryClass}
        if not isinstance(operating_classes, list) or "SPOT" not in operating_classes or not set(operating_classes).issubset(valid_inventory_classes):
            gate["eligible"] = False
            return self._pending(definitions, gate, "inventory_caliber 未配置 operating_classes，至少必须包含 SPOT")
        records = self.database.list_inventory_facts(sku)
        if not records:
            gate["eligible"] = False
            return self._pending(definitions, gate, "库存事实尚未接入")
        unmapped = []
        spot_qty = transit_qty = operating_amount = 0.0
        traces = []
        warehouse_version = self.database.published_version("warehouse_mapping")
        for record in records:
            warehouse = warehouse_map.get(str(record.get("warehouse_raw_name")))
            sku_value = sku_map.get(str(record.get("sku_raw")))
            if not warehouse or not warehouse.get("canonical"):
                unmapped.append("warehouse_mapping:{}".format(record.get("warehouse_raw_name")))
                continue
            if not sku_value or not sku_value.get("canonical"):
                unmapped.append("sku_mapping:{}".format(record.get("sku_raw")))
                continue
            classification = str(warehouse.get("inventory_class", ""))
            if classification not in {item.value for item in InventoryClass}:
                unmapped.append("warehouse_mapping:{}缺少inventory_class".format(record.get("warehouse_raw_name")))
                continue
            traces.append({"source_api": record.get("source_api"), "warehouse_raw_name": record.get("warehouse_raw_name"), "mapping_version": warehouse_version["version_name"], "inventory_class": classification})
            if classification == InventoryClass.SPOT.value:
                spot_qty += float(record.get("quantity") or 0)
                operating_amount += float(record.get("amount") or 0)
            elif classification == InventoryClass.IN_TRANSIT.value and "IN_TRANSIT" in operating_classes:
                transit_qty += float(record.get("quantity") or 0)
                operating_amount += float(record.get("amount") or 0)
        if unmapped:
            gate.update({"eligible": False, "unmapped_facts": sorted(set(unmapped))})
            return self._pending(definitions, gate, "存在未确认仓库/SKU或未发布库存归类")
        updated_at = max((str(record.get("synced_at") or "") for record in records), default=None)
        values = (round(spot_qty, 4), round(transit_qty, 4), round(spot_qty + transit_qty, 4), round(operating_amount, 2))
        return {"mode": "formal", "data": [self._metric(item, value, "正式", updated_at) for item, value in zip(definitions, values)], "gate": gate, "message": "已按发布版本计算", "generated_business_data": False, "source_record_count": len(records), "trace": traces}

    def woi_summary(self, sku: str = "", filters: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
        definitions = self._definitions(("spot_woi", "operating_woi"))
        gate = self._gate(definitions)
        requested = dict(filters or {})
        unsupported = [name for name in ("business_unit", "brand") if requested.get(name)]
        if requested.get("compare") not in (None, "", "none"):
            unsupported.append("compare")
        if unsupported:
            gate.update({"eligible": False, "pending_filter_fields": unsupported})
            return self._pending(definitions, gate, "筛选字段尚未进入事实合同")
        if not gate["eligible"]:
            return self._pending(definitions, gate)
        sales_source = self.database.list_sales_facts(sku)
        if not sales_source:
            gate["eligible"] = False
            return self._pending(definitions, gate, "WOI 所需销售事实尚未接入")
        sales_records, context = self._sales_context(sales_source)
        if requested.get("channel"):
            sales_records = [record for record in sales_records if requested["channel"] in {str(record.get("channel_raw_name")), str(record.get("canonical_channel"))}]
        inventory = self.inventory_summary(sku, filters)
        if context["unmapped"] or context["reason"] or not inventory["gate"]["eligible"]:
            gate.update({"eligible": False, "unmapped_facts": sorted(set(context["unmapped"] + inventory["gate"].get("unmapped_facts", [])))})
            return self._pending(definitions, gate, "WOI 所需事实仍有未确认项")
        caliber_entries = _version_map(self.database.published_version("sales_caliber"))
        settings = caliber_entries.get("default") or next(iter(caliber_entries.values()), {})
        try:
            window_days = int(settings.get("woi_window_days", 28))
            if window_days < 1:
                raise ValueError
        except (TypeError, ValueError):
            gate["eligible"] = False
            return self._pending(definitions, gate, "sales_caliber 的 woi_window_days 必须为正整数")
        parsed = [(record, _parse_time(record.get("metric_time"))) for record in sales_records]
        available_dates = [value for _, value in parsed if value]
        as_of = max(available_dates) if available_dates else datetime.now(timezone.utc)
        start = as_of - timedelta(days=window_days - 1)
        quantity = sum(record["metric_quantity"] for record, date in parsed if date and start <= date <= as_of)
        inventory_by_code = {item["code"]: item["value"] for item in inventory["data"]}
        calculated = calculate_dual_woi(float(inventory_by_code["spot_inventory_qty"]), float(inventory_by_code["in_transit_inventory_qty"]), quantity, window_days)
        updated_at = max((str(record.get("synced_at") or "") for record in sales_records), default=None)
        details = {"state": calculated["state"], "window_days": window_days, "sales_quantity": round(quantity, 4)}
        return {"mode": "formal", "data": [self._metric(definitions[0], calculated["spot"], "正式", updated_at, details), self._metric(definitions[1], calculated["operating"], "正式", updated_at, details)], "gate": gate, "message": "已按发布版本计算", "generated_business_data": False}

    def sku_detail(self, sku: str, filters: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
        sales = self.sales_summary(sku, filters)
        inventory = self.inventory_summary(sku, filters)
        woi = self.woi_summary(sku, filters)
        windows: Dict[str, Any] = {}
        records, _ = self._sales_context(self.database.list_sales_facts(sku)) if sales["gate"]["eligible"] else ([], {})
        if filters and filters.get("channel"):
            records = [record for record in records if filters["channel"] in {str(record.get("channel_raw_name")), str(record.get("canonical_channel"))}]
        parsed = [(record, _parse_time(record.get("metric_time"))) for record in records]
        dates = [value for _, value in parsed if value]
        as_of = max(dates) if dates else None
        for days in (7, 14, 28, 90):
            if as_of:
                start = as_of - timedelta(days=days - 1)
                windows[str(days)] = round(sum(record["metric_quantity"] for record, date in parsed if date and start <= date <= as_of), 4)
            else:
                windows[str(days)] = None
        dimensions = {"channels": sorted({str(row.get("channel_raw_name") or "") for row in self.database.list_sales_facts(sku)} - {""}), "warehouses": sorted({str(row.get("warehouse_raw_name") or "") for row in self.database.list_inventory_facts(sku)} - {""})}
        return {"sku": sku, "sales": sales, "inventory": inventory, "woi": woi, "sales_windows": windows, "dimensions": dimensions, "aging": "待接入", "price": "待接入", "dg_policy": "待接入"}

    def purchase_summary(self, filters: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
        definitions = self._definitions(("purchase_open_qty",))
        gate = self._gate(definitions)
        requested = {key: value for key, value in dict(filters or {}).items() if value not in (None, "", "none")}
        if requested:
            gate.update({"eligible": False, "pending_filter_fields": sorted(requested)})
        return self._pending(definitions, gate, "采购事实尚未接入")

    def policy_summary(self) -> Dict[str, Any]:
        return {"mode": "formal", "data": [], "message": "待接入", "reason": "Apple 政策条款、期间、返点及适用范围尚未接入和确认", "generated_business_data": False}
