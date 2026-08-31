"""纯 Mock 演示适配器。

本模块只在 DEMO_MODE=true 时启用。所有记录均为虚构的流程验证数据，
不会读取吉客云、APR、客流爬虫、正式事实库或 Sandbox 快照。
"""

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import threading
from typing import Any, Dict, Iterable, List, Mapping


DEMO_LABEL = "演示数据，仅用于页面及流程验证"
DEMO_SOURCE = "DEMO Adapter（纯 Mock）"
BUSINESS_UNITS = (
    "Apple线下/APR",
    "Apple电商",
    "Shure电商",
    "Apple渠道",
)
CHANNELS = (
    "APR门店", "O2O / 即时零售", "羽通 - 京东", "啟韬 - 苏宁",
    "京东", "天猫", "3PP", "分销",
)


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).replace(microsecond=0).isoformat()


def _metric(name: str, value: Any, unit: str, caliber: str, code: str = "") -> Dict[str, Any]:
    return {
        "code": code,
        "name": name,
        "value": value,
        "unit": unit,
        "caliber": caliber,
        "source": DEMO_SOURCE,
        "updated_at": _now(),
        "conflict": False,
        "status": "演示",
        "data_class": "DEMO",
    }


def _envelope(**payload: Any) -> Dict[str, Any]:
    return {
        **payload,
        "mode": "demo",
        "data_class": "DEMO",
        "label": DEMO_LABEL,
        "formal_kpi_enabled": False,
        "real_system_connected": False,
        "generated_business_data": True,
    }


class DemoAdapter:
    """提供可交互但绝不冒充正式经营数据的内存演示数据。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._next_version = 100
        self._review_items = self._build_review_items()
        self._versions = [
            {
                "id": 91,
                "version_type": "sku_mapping",
                "version_name": "demo_sku_mapping_v1",
                "status": "PUBLISHED",
                "reason": "演示人工确认与发布链路",
                "affected_metrics": ["SKU 360", "库存结构"],
                "confirmed_by": "demo-po",
                "confirmed_at": "2026-08-30T09:10:00+08:00",
                "published_by": "demo-po",
                "published_at": "2026-08-30T09:12:00+08:00",
                "data_class": "DEMO",
            }
        ]

    @staticmethod
    def context() -> Dict[str, Any]:
        return _envelope(
            service="采销经营驾驶舱 V1",
            banner=DEMO_LABEL,
            demo_mode=True,
            filters={
                "business_units": list(BUSINESS_UNITS),
                "brands": ["Apple", "Shure"],
                "channels": list(CHANNELS),
                "compare_modes": ["不对比", "环比/上一周期", "同比", "目标", "差额"],
            },
            isolation={
                "FORMAL": "仅接收人工确认并发布后的真实事实、映射与口径；当前未接入",
                "SANDBOX": "只用于快照与差异验证，不进入正式 KPI",
                "DEMO": "只读取纯 Mock Demo Adapter，不调用真实系统",
            },
        )

    @staticmethod
    def boards() -> List[Dict[str, str]]:
        return [
            {"code": "overview", "name": "经营总览", "path": "/cx/"},
            {"code": "products", "name": "商品经营", "path": "/cx/products"},
            {"code": "inventory_purchase", "name": "库存与采购", "path": "/cx/inventory"},
            {"code": "policy", "name": "政策经营", "path": "/cx/policy/dg"},
            {"code": "actions", "name": "行动中心", "path": "/cx/actions"},
        ]

    @staticmethod
    def _skus() -> List[Dict[str, Any]]:
        return [
            {
                "sku": "DEMO-APL-PH-001", "spu": "DEMO-APL-PH", "name": "Apple 演示手机 A1",
                "brand": "Apple", "category": "手机", "business_unit": "Apple线下/APR", "channel": "APR门店",
                "lifecycle": "在售", "price": 6999, "cost": 5600, "gross_profit": 1399, "gross_margin": 19.99,
                "sales_windows": {"7": 18, "14": 36, "28": 72, "90": 228},
                "spot": 36, "in_transit": 24, "operating": 60, "spot_woi": 2.0, "operating_woi": 3.33,
                "aging": {"<90": 28, "90-180": 6, "180-360": 2, "360+": 0},
                "dg": "DG SI / ST 演示范围", "policy": "演示政策版本 demo-policy-v1",
                "channels": [{"name": "APR门店", "sales": 54}, {"name": "O2O / 即时零售", "sales": 18}],
                "warehouses": [{"name": "APR演示正品仓01", "spot": 22}, {"name": "APR演示正品仓02", "spot": 14}],
            },
            {
                "sku": "DEMO-APL-TAB-002", "spu": "DEMO-APL-TAB", "name": "Apple 演示平板 B2",
                "brand": "Apple", "category": "平板", "business_unit": "Apple电商", "channel": "羽通 - 京东",
                "lifecycle": "在售", "price": 4299, "cost": 3500, "gross_profit": 799, "gross_margin": 18.59,
                "sales_windows": {"7": 12, "14": 25, "28": 48, "90": 156},
                "spot": 15, "in_transit": 28, "operating": 43, "spot_woi": 1.25, "operating_woi": 3.58,
                "aging": {"<90": 11, "90-180": 4, "180-360": 0, "360+": 0},
                "dg": "DG ST 演示范围", "policy": "演示电商政策 demo-policy-v1",
                "channels": [{"name": "羽通 - 京东", "sales": 31}, {"name": "啟韬 - 苏宁", "sales": 17}],
                "warehouses": [{"name": "电商演示仓01", "spot": 15}],
            },
            {
                "sku": "DEMO-SHU-AUD-003", "spu": "DEMO-SHU-AUD", "name": "Shure 演示无线音频 S1",
                "brand": "Shure", "category": "音频", "business_unit": "Shure电商", "channel": "天猫",
                "lifecycle": "在售", "price": 2899, "cost": 1980, "gross_profit": 919, "gross_margin": 31.70,
                "sales_windows": {"7": 7, "14": 15, "28": 31, "90": 98},
                "spot": 45, "in_transit": 10, "operating": 55, "spot_woi": 5.81, "operating_woi": 7.10,
                "aging": {"<90": 18, "90-180": 13, "180-360": 9, "360+": 5},
                "dg": "不适用", "policy": "Shure 演示动销规则",
                "channels": [{"name": "天猫", "sales": 20}, {"name": "京东", "sales": 11}],
                "warehouses": [{"name": "Shure演示正品仓", "spot": 45}],
            },
            {
                "sku": "DEMO-APL-ACC-004", "spu": "DEMO-APL-ACC", "name": "Apple 演示配件 C3",
                "brand": "Apple", "category": "配件", "business_unit": "Apple渠道", "channel": "3PP",
                "lifecycle": "在售", "price": 799, "cost": 520, "gross_profit": 279, "gross_margin": 34.92,
                "sales_windows": {"7": 2, "14": 4, "28": 7, "90": 28},
                "spot": 86, "in_transit": 0, "operating": 86, "spot_woi": 49.14, "operating_woi": 49.14,
                "aging": {"<90": 16, "90-180": 20, "180-360": 30, "360+": 20},
                "dg": "DG SI 演示范围", "policy": "3PP 演示政策待人工复核",
                "channels": [{"name": "3PP", "sales": 4}, {"name": "分销", "sales": 3}],
                "warehouses": [{"name": "渠道演示仓", "spot": 86}],
            },
        ]

    @staticmethod
    def dimensions(entity_type: str) -> List[Dict[str, Any]]:
        skus = DemoAdapter._skus()
        if entity_type == "sku_mapping":
            return [
                {"source_key": item["sku"], "value": {"canonical": item["sku"], "display_name": item["name"]}, "version": "demo_sku_mapping_v1", "data_class": "DEMO"}
                for item in skus
            ]
        if entity_type == "channel_mapping":
            return [{"source_key": value, "value": {"canonical": value, "display_name": value}, "version": "demo_channel_mapping_v1", "data_class": "DEMO"} for value in CHANNELS]
        if entity_type == "warehouse_mapping":
            names = sorted({warehouse["name"] for sku in skus for warehouse in sku["warehouses"]})
            return [{"source_key": value, "value": {"canonical": value, "display_name": value}, "version": "demo_warehouse_mapping_v1", "data_class": "DEMO"} for value in names]
        return []

    @staticmethod
    def sales_summary(filters: Mapping[str, str]) -> Dict[str, Any]:
        scope = DemoAdapter._scope(filters)
        return _envelope(
            data=[
                _metric("销售额", 1286420, "元", "演示付款口径 demo_sales_caliber_v1", "sales_amount"),
                _metric("销售数量", 438, "台", "演示净销量，调整规则仅用于流程验证", "sales_quantity"),
                _metric("销售目标", 1500000, "元", "演示目标台账 demo_target_v1", "sales_target"),
                _metric("目标达成率", 85.76, "%", "销售额 / 演示目标", "target_rate"),
                _metric("毛利额", 262300, "元", "演示成本与售价，不代表真实毛利", "gross_profit"),
                _metric("毛利率", 20.39, "%", "演示毛利额 / 演示销售额", "gross_margin"),
            ],
            scope=scope,
            gate={"eligible": False, "gate": "DEMO_ONLY", "missing": ["正式事实与发布版本"]},
        )

    @staticmethod
    def sales_daily(filters: Mapping[str, str]) -> Dict[str, Any]:
        rows = []
        today = date.today()
        for index in range(13, -1, -1):
            day = today - timedelta(days=index)
            amount = 64200 + ((13 - index) % 5) * 7100 + ((13 - index) % 3) * 2900
            rows.append({"date": day.isoformat(), "sales_amount": amount, "order_count": 18 + ((13 - index) % 7), "quantity": 24 + ((13 - index) % 9), "caliber": "演示付款口径", "data_class": "DEMO"})
        return _envelope(rows=rows, data=rows, scope=DemoAdapter._scope(filters), message="演示按日销售趋势")

    @staticmethod
    def inventory_summary(filters: Mapping[str, str]) -> Dict[str, Any]:
        return _envelope(
            data=[
                _metric("现货库存", 182, "台", "演示已发布仓库映射中的现货", "spot_inventory"),
                _metric("在途库存", 62, "台", "演示采购/调拨在途规则", "in_transit_inventory"),
                _metric("经营库存", 244, "台", "现货 + 符合演示规则的在途", "operating_inventory"),
            ],
            scope=DemoAdapter._scope(filters),
            gate={"eligible": False, "gate": "DEMO_ONLY", "missing": ["正式库存事实与发布版本"]},
        )

    @staticmethod
    def inventory_aging() -> Dict[str, Any]:
        rows = [
            {"bucket": "<90", "quantity": 73, "amount": 256400, "ratio": 40.1, "status": "演示"},
            {"bucket": "90-180", "quantity": 43, "amount": 132600, "ratio": 23.6, "status": "演示"},
            {"bucket": "180-360", "quantity": 41, "amount": 104800, "ratio": 22.5, "status": "演示"},
            {"bucket": "360+", "quantity": 25, "amount": 61800, "ratio": 13.8, "status": "演示"},
        ]
        return _envelope(rows=rows, data=rows, source=DEMO_SOURCE, updated_at=_now(), confirmation_status="DEMO_PUBLISHED")

    @staticmethod
    def purchase_summary(filters: Mapping[str, str]) -> Dict[str, Any]:
        steps = [
            {"name": "需求", "count": 12, "status": "演示"}, {"name": "采购单", "count": 8, "status": "演示"},
            {"name": "在途", "count": 5, "status": "演示"}, {"name": "到货", "count": 3, "status": "演示"},
            {"name": "入库", "count": 2, "status": "演示"}, {"name": "分配", "count": 7, "status": "演示"},
            {"name": "门店/渠道", "count": 7, "status": "演示"},
        ]
        orders = [
            {"code": "DEMO-PO-001", "sku": "DEMO-APL-TAB-002", "warehouse": "电商演示仓01", "quantity": 20, "status": "在途", "eta": "2026-09-03", "source": DEMO_SOURCE},
            {"code": "DEMO-TR-002", "sku": "DEMO-APL-PH-001", "warehouse": "APR演示正品仓02", "quantity": 12, "status": "待分配", "eta": "2026-09-01", "source": DEMO_SOURCE},
            {"code": "DEMO-PO-003", "sku": "DEMO-SHU-AUD-003", "warehouse": "Shure演示正品仓", "quantity": 10, "status": "待到货", "eta": "2026-09-05", "source": DEMO_SOURCE},
        ]
        return _envelope(
            data=[_metric("在途采购", 5, "单", "演示采购/调拨单据", "open_purchase"), _metric("预计到货", 42, "台", "演示ETA范围内数量", "eta_quantity")],
            flow_steps=steps, orders=orders, scope=DemoAdapter._scope(filters),
        )

    @staticmethod
    def policy_summary() -> Dict[str, Any]:
        items = [
            {"code": "DEMO-DG-SI", "name": "DG SI（Sell-in）", "target": 720000, "actual": 598000, "rate": 83.06, "period": "演示周期", "scope": "演示 SKU/SPU 范围", "risk": "差额 122000 元", "source": DEMO_SOURCE},
            {"code": "DEMO-DG-ST", "name": "DG ST（Sell-through）", "target": 610, "actual": 492, "rate": 80.66, "period": "演示周期", "scope": "演示终端动销范围", "risk": "差额 118 台", "source": DEMO_SOURCE},
            {"code": "DEMO-STORE-SUBSIDY", "name": "单店补贴", "target": 10, "actual": 7, "rate": 70.0, "period": "演示周期", "scope": "10 家演示门店", "risk": "3 家门店待复核", "source": DEMO_SOURCE},
        ]
        dg_tasks = [
            {"task": "DG SI · 手机产品组", "type": "DG SI", "product": "手机", "target": 420000, "actual": 371000, "rate": 88.33, "time_progress": 76.67, "gap": 49000, "deadline": "2026-09-30", "status": "关注"},
            {"task": "DG SI · 平板产品组", "type": "DG SI", "product": "平板", "target": 300000, "actual": 227000, "rate": 75.67, "time_progress": 76.67, "gap": 73000, "deadline": "2026-09-30", "status": "落后"},
            {"task": "DG ST · 手机产品组", "type": "DG ST", "product": "手机", "target": 360, "actual": 318, "rate": 88.33, "time_progress": 76.67, "gap": 42, "deadline": "2026-09-30", "status": "正常"},
            {"task": "DG ST · 平板产品组", "type": "DG ST", "product": "平板", "target": 250, "actual": 174, "rate": 69.60, "time_progress": 76.67, "gap": 76, "deadline": "2026-09-30", "status": "严重落后"},
        ]
        store_subsidies = [
            {"store": "APR演示门店01", "category": "Mac", "target": 28, "actual": 25, "rate": 89.29, "time_progress": 76.67, "gap": 3, "forecast": 32, "status": "领先时间进度"},
            {"store": "APR演示门店02", "category": "Watch", "target": 34, "actual": 26, "rate": 76.47, "time_progress": 76.67, "gap": 8, "forecast": 34, "status": "接近时间进度"},
            {"store": "APR演示门店03", "category": "Mac", "target": 30, "actual": 20, "rate": 66.67, "time_progress": 76.67, "gap": 10, "forecast": 26, "status": "落后"},
            {"store": "APR演示门店04", "category": "Watch", "target": 40, "actual": 23, "rate": 57.50, "time_progress": 76.67, "gap": 17, "forecast": 30, "status": "严重落后"},
            {"store": "APR演示门店05", "category": "Mac", "target": 22, "actual": 19, "rate": 86.36, "time_progress": 76.67, "gap": 3, "forecast": 25, "status": "领先时间进度"},
            {"store": "APR演示门店06", "category": "Watch", "target": 36, "actual": 28, "rate": 77.78, "time_progress": 76.67, "gap": 8, "forecast": 37, "status": "接近时间进度"},
            {"store": "APR演示门店07", "category": "Mac", "target": 26, "actual": 16, "rate": 61.54, "time_progress": 76.67, "gap": 10, "forecast": 21, "status": "落后"},
            {"store": "APR演示门店08", "category": "Watch", "target": 32, "actual": 15, "rate": 46.88, "time_progress": 76.67, "gap": 17, "forecast": 20, "status": "严重落后"},
            {"store": "APR演示门店09", "category": "Mac", "target": 24, "actual": 21, "rate": 87.50, "time_progress": 76.67, "gap": 3, "forecast": 27, "status": "领先时间进度"},
            {"store": "APR演示门店10", "category": "Watch", "target": 38, "actual": 29, "rate": 76.32, "time_progress": 76.67, "gap": 9, "forecast": 38, "status": "接近时间进度"},
        ]
        return _envelope(
            data=[
                _metric("DG SI 达成率", 83.06, "%", "演示 Sell-in 目标 / 实际", "dg_si_rate"),
                _metric("DG ST 达成率", 80.66, "%", "演示 Sell-through 目标 / 实际", "dg_st_rate"),
                _metric("单店补贴覆盖", 7, "店", "演示独立补贴台账", "store_subsidy"),
            ],
            items=items, dg_tasks=dg_tasks, store_subsidies=store_subsidies,
            rebate_items=[
                {"name": "价格政策", "status": "待接入"},
                {"name": "国补", "status": "待接入"},
                {"name": "返利", "status": "待接入"},
                {"name": "采购激励", "status": "待接入"},
                {"name": "销售激励", "status": "待接入"},
            ],
            future_policies=["价格保护", "市场基金", "返利政策", "其他品牌政策"],
            reason="三类政策独立展示，不能混算",
        )

    @staticmethod
    def anomaly_list() -> Dict[str, Any]:
        data = [
            {"id": "DEMO-RISK-001", "type": "缺货", "sku": "DEMO-APL-TAB-002", "level": "高", "status": "待确认", "evidence": "演示近28天销量与现货结构显示补货风险", "threshold": "演示阈值 v1", "ai": DemoAdapter._ai("现货覆盖偏低", "近28天销量48台，现货15台", "补货节奏可能晚于销售节奏", "复核在途ETA并准备补货方案")},
            {"id": "DEMO-RISK-002", "type": "高库存", "sku": "DEMO-APL-ACC-004", "level": "高", "status": "待确认", "evidence": "演示经营库存86台，含在途WOI 49.14周", "threshold": "演示阈值 v1", "ai": DemoAdapter._ai("经营库存偏高", "近28天销量7台，现货86台", "渠道动销不及演示计划", "复核调拨、分销或促销动作")},
            {"id": "DEMO-RISK-003", "type": "长库龄", "sku": "DEMO-SHU-AUD-003", "level": "中", "status": "待确认", "evidence": "演示180天以上库存14台", "threshold": "演示阈值 v1", "ai": DemoAdapter._ai("长库龄占比偏高", "180天以上14台", "历史备货与当前动销不匹配", "按渠道复核慢动销SKU")},
            {"id": "DEMO-RISK-004", "type": "DG风险", "sku": "DEMO-APL-PH-001", "level": "中", "status": "待确认", "evidence": "演示DG SI与ST均有差额", "threshold": "演示政策 v1", "ai": DemoAdapter._ai("政策达成存在差额", "SI 83.06%，ST 80.66%", "结构性缺货或渠道分配可能影响达成", "复核可供货SKU与重点门店分配")},
            {"id": "DEMO-RISK-005", "type": "补贴风险", "sku": "", "level": "中", "status": "待确认", "evidence": "3家演示门店未覆盖", "threshold": "演示补贴 v1", "ai": DemoAdapter._ai("单店补贴覆盖不足", "10家演示门店中7家达成", "门店目标或证明材料可能待核", "逐店复核补贴条件与资料")},
        ]
        return _envelope(data=data, threshold_status="DEMO_PUBLISHED", approval_required=True)

    @staticmethod
    def action_list() -> Dict[str, Any]:
        data = [
            {"action_code": "DEMO-ACT-001", "title": "复核平板B2在途ETA并准备补货", "action_type": "补货", "sku": "DEMO-APL-TAB-002", "status": "待确认", "owner": "待PO指定", "due_at": "2026-09-01", "source_reference": "DEMO-RISK-001"},
            {"action_code": "DEMO-ACT-002", "title": "复核配件C3跨渠道调拨可行性", "action_type": "调拨", "sku": "DEMO-APL-ACC-004", "status": "已确认", "owner": "演示责任人", "due_at": "2026-09-02", "source_reference": "DEMO-RISK-002"},
            {"action_code": "DEMO-ACT-003", "title": "形成Shure慢动销清理建议", "action_type": "继续观察", "sku": "DEMO-SHU-AUD-003", "status": "执行中", "owner": "演示责任人", "due_at": "2026-09-05", "source_reference": "DEMO-RISK-003"},
        ]
        return _envelope(data=data, message="演示动作台账", approval_required=True)

    @staticmethod
    def traffic_summary() -> Dict[str, Any]:
        stores = [
            {"date": date.today().isoformat(), "store": "APR演示门店01", "traffic": 126, "source": "手工演示上传", "updated_at": _now()},
            {"date": date.today().isoformat(), "store": "APR演示门店02", "traffic": 98, "source": "自动演示接口", "updated_at": _now()},
            {"date": date.today().isoformat(), "store": "APR演示门店03", "traffic": 87, "source": "手工演示上传", "updated_at": _now()},
        ]
        return _envelope(data=stores, contract_fields=["date", "store", "traffic", "source", "updated_at"], automation_connected=False)

    @staticmethod
    def sku_detail(sku: str, filters: Mapping[str, str]) -> Dict[str, Any]:
        item = next((value for value in DemoAdapter._skus() if value["sku"] == sku), None)
        if item is None:
            return _envelope(
                sku=sku, found=False, message="演示数据中未找到该 SKU",
                sales={"data": []}, inventory={"data": []}, woi={"data": []}, sales_windows={},
            )
        return _envelope(
            sku=item["sku"], found=True, master={key: item[key] for key in ("sku", "spu", "name", "brand", "category", "business_unit", "channel", "lifecycle")},
            sales_windows=item["sales_windows"],
            sales={"data": [_metric("近28天销量", item["sales_windows"]["28"], "台", "演示付款销售口径"), _metric("演示销售额", item["sales_windows"]["28"] * item["price"], "元", "演示数量 × 演示售价")]},
            inventory={"data": [_metric("现货库存", item["spot"], "台", "演示现货分类"), _metric("在途库存", item["in_transit"], "台", "演示在途分类"), _metric("经营库存", item["operating"], "台", "演示现货 + 在途")]},
            woi={"data": [_metric("现货WOI", item["spot_woi"], "周", "近28天演示销量"), _metric("含在途WOI", item["operating_woi"], "周", "近28天演示销量")]},
            price={"selling": item["price"], "cost": item["cost"], "gross_profit": item["gross_profit"], "gross_margin": item["gross_margin"], "status": "演示"},
            aging=item["aging"], dimensions={"channels": item["channels"], "warehouses": item["warehouses"]},
            dg_policy=item["dg"], policy=item["policy"], risk=next((risk for risk in DemoAdapter.anomaly_list()["data"] if risk["sku"] == sku), None),
            source=DEMO_SOURCE, updated_at=_now(), scope=DemoAdapter._scope(filters),
        )

    @staticmethod
    def api_cards() -> List[Dict[str, Any]]:
        common = {
            "configured": False, "missing": ["正式API文档", "鉴权", "分页", "限流", "源记录ID"],
            "endpoint": "正式地址待接入", "auth": "真实鉴权未配置", "pagination": "待联调确认",
            "rate_limit": "待联调确认", "retry": "退避、幂等和死信策略待确认", "formal_kpi_enabled": False,
            "pipeline": ["原始API数据", "清洗", "映射", "指标计算"], "data_class": "DEMO",
        }
        cards = []
        for domain, name, purpose, fields in (
            ("sales", "销售 API", "订单事实、状态与五时间口径复核", ["trade_no", "line_id", "create_time", "pay_time", "audit_time", "consign_time", "complete_time", "modified_time", "trade_status", "payment"]),
            ("inventory", "库存 API", "现货、在途、经营库存与仓库映射复核", ["sku", "warehouse_raw_name", "quantity", "locked_quantity", "available_quantity", "snapshot_at"]),
            ("purchase", "采购 API", "采购单、在途、ETA、到货与入库状态复核", ["purchase_no", "sku", "quantity", "status", "eta", "warehouse_raw_name"]),
            ("transfer", "调拨 API", "调出、在途、调入与门店/渠道分配复核", ["transfer_no", "sku", "from_warehouse", "to_warehouse", "quantity", "status"]),
        ):
            cards.append({**common, "domain": domain, "name": name, "purpose": purpose, "business_question": "PO需要确认该接口能否稳定支持经营链路", "required_fields": fields, "status": "待PO/WorkBuddy联调", "sync_logic": "modified或等同更新时间优先；不稳定时滚动回溯 + upsert", "statistics_logic": "与同步窗口分离，由已发布口径版本选择统计时间"})
        return cards

    @staticmethod
    def sandbox_overview() -> Dict[str, Any]:
        return {
            "mode": "sandbox", "data_class": "SANDBOX", "label": "验证数据，不代表正式经营口径",
            "formal_kpi_enabled": False, "real_system_connected": False,
            "snapshot": {"status": "演示差异集已就绪", "label": "Demo预置差异；不读取真实快照", "files": []},
            "formal": {"message": "待接入", "values_exposed": False, "gate": {"eligible": False, "gate": "FORMAL_REQUIRED_VERSIONS_MISSING", "missing": ["正式事实", "正式映射", "正式口径"]}},
            "preset": {
                "sales": {"old_sales_amount": 918000, "new_sales_amount": 946500, "difference": 28500, "difference_rate": 3.10, "different_orders": 17, "only_old": 5, "only_new": 9, "amount_mismatch": 3, "channel_differences": 4, "store_differences": 6, "sku_differences": 8},
                "inventory": {"quantity_difference": -38, "amount_difference": -118600, "warehouse_differences": 5, "sku_differences": 12, "mapping_differences": 4},
            },
            "isolation": "Sandbox 数据不得进入正式 KPI；Demo 预置差异也不得进入正式经营视图",
        }

    def review_items(self, entity_type: str = "", status: str = "") -> List[Dict[str, Any]]:
        with self._lock:
            values = deepcopy(self._review_items)
        if entity_type:
            values = [item for item in values if item["entity_type"] == entity_type]
        if status:
            values = [item for item in values if item["status"] == status]
        return values

    def versions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return deepcopy(self._versions)

    def confirm(self, body: Mapping[str, Any], actor: str) -> Dict[str, Any]:
        item_ids = {int(value) for value in body.get("item_ids", [])}
        decisions = {int(item["item_id"]): item for item in body.get("decisions", []) if isinstance(item, dict) and item.get("item_id")}
        if not item_ids:
            raise ValueError("至少选择一个演示复核对象")
        with self._lock:
            matching = [item for item in self._review_items if item["id"] in item_ids]
            if len(matching) != len(item_ids):
                raise ValueError("演示复核对象不存在")
            for item in matching:
                decision = decisions.get(item["id"], {})
                display_name = str(decision.get("display_name") or item["suggested_display_name"]).strip()
                if not display_name:
                    raise ValueError("display_name 必须由人工确认")
                item.update({
                    "display_name": display_name,
                    "business_unit": str(decision.get("business_unit") or ""),
                    "channel": str(decision.get("channel") or ""),
                    "store_shop": str(decision.get("store_shop") or ""),
                    "inventory_class": str(decision.get("inventory_class") or ""),
                    "status": "PUBLISHED" if body.get("publish") else "CONFIRMED",
                    "version": str(body.get("version_name") or "demo_version"),
                })
            version = {
                "id": self._next_version, "version_type": str(body.get("version_type") or ""),
                "version_name": str(body.get("version_name") or ""), "status": "PUBLISHED" if body.get("publish") else "DRAFT",
                "reason": str(body.get("reason") or ""), "affected_metrics": list(body.get("affected_metrics") or []),
                "confirmed_by": actor, "confirmed_at": _now(), "published_by": actor if body.get("publish") else None,
                "published_at": _now() if body.get("publish") else None, "data_class": "DEMO",
                "before": [{"item_id": item["id"], "status": "UNCONFIRMED"} for item in matching],
                "after": [{"item_id": item["id"], "status": item["status"], "display_name": item["display_name"]} for item in matching],
            }
            self._next_version += 1
            self._versions.insert(0, version)
            return deepcopy(version)

    def publish(self, version_id: int, actor: str) -> Dict[str, Any]:
        with self._lock:
            version = next((item for item in self._versions if item["id"] == version_id), None)
            if version is None:
                raise ValueError("演示版本不存在")
            version["status"] = "PUBLISHED"
            version["published_by"] = actor
            version["published_at"] = _now()
            for item in self._review_items:
                if item.get("version") == version["version_name"]:
                    item["status"] = "PUBLISHED"
            return deepcopy(version)

    @staticmethod
    def _scope(filters: Mapping[str, str]) -> str:
        parts = [str(filters.get(name, "")).strip() for name in ("business_unit", "brand", "channel")]
        return " / ".join(value for value in parts if value) or "全部演示经营范围"

    @staticmethod
    def _ai(problem: str, evidence: str, reason: str, action: str) -> Dict[str, str]:
        return {
            "problem": problem, "evidence": evidence, "possible_causes": reason,
            "suggested_action": action, "pending_confirmation": "以上均为演示解释与建议，需人工确认后才能形成动作",
        }

    @staticmethod
    def _build_review_items() -> List[Dict[str, Any]]:
        rows = [
            (9001, "warehouse_mapping", "DEMO-WH-RAW-01", "演示原始仓库甲", "APR演示正品仓01", "SPOT"),
            (9002, "warehouse_mapping", "DEMO-WH-RAW-02", "演示原始仓库乙", "电商演示在途仓", "IN_TRANSIT"),
            (9003, "channel_mapping", "DEMO-CH-RAW-01", "演示原始渠道甲", "APR门店", ""),
            (9004, "channel_mapping", "DEMO-CH-RAW-02", "演示原始渠道乙", "羽通-JD", ""),
            (9005, "sku_mapping", "DEMO-SKU-RAW-01", "演示原始商品甲", "Apple 演示手机 A1", ""),
            (9006, "sales_caliber", "DEMO-CAL-SALE", "演示销售口径", "付款时间净销售演示口径", ""),
            (9007, "inventory_caliber", "DEMO-CAL-INV", "演示库存口径", "现货/在途/经营库存演示口径", ""),
            (9008, "sales_adjustment_rules", "DEMO-ADJ-01", "演示退货状态", "OFFSET（演示建议）", ""),
        ]
        return [
            {
                "id": row[0], "entity_type": row[1], "source_system": "demo", "source_key": row[2],
                "raw_code": row[2], "raw_name": row[3], "history_mapping": [{"display_name": "演示历史映射", "effective_to": "2026-08-01"}],
                "suggested_display_name": row[4], "display_name": "", "business_unit": "", "channel": "", "store_shop": "",
                "inventory_class": row[5], "status": "UNCONFIRMED", "version": "", "data_class": "DEMO",
            }
            for row in rows
        ]
