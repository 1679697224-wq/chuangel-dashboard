"""正式经营指标查询；缺真实数据或发布版本时统一返回“待接入”。"""

from typing import Any, Dict, Iterable, List

from ..models import pending_metric
from .review import ReviewService


METRIC_DICTIONARY = [
    {
        "code": "sales_amount",
        "name": "销售额",
        "caliber": "付款时间；仅已付款订单；金额字段及退款处理待业务确认",
        "source": "吉客云 API（待联调）",
        "unit": "元",
        "required_versions": ["sales_caliber", "channel_mapping", "sku_mapping"],
    },
    {
        "code": "paid_orders",
        "name": "已付款订单数",
        "caliber": "按付款时间统计，订单去重键待业务确认",
        "source": "吉客云 API（待联调）",
        "unit": "单",
        "required_versions": ["sales_caliber", "channel_mapping"],
    },
    {
        "code": "inventory_qty",
        "name": "库存数量",
        "caliber": "三视图并列，仓库/库位/可用量细则待业务确认",
        "source": "吉客云 API（待联调）",
        "unit": "台",
        "required_versions": ["inventory_caliber", "warehouse_mapping", "sku_mapping"],
    },
    {
        "code": "inventory_value",
        "name": "库存金额",
        "caliber": "成本字段与计价方法待业务确认",
        "source": "吉客云 API（待联调）",
        "unit": "元",
        "required_versions": ["inventory_caliber", "warehouse_mapping", "sku_mapping"],
    },
    {
        "code": "woi_28d",
        "name": "双口径周转周数",
        "caliber": "库存数量或库存金额 ÷（近28天日均销量或销额×7）",
        "source": "吉客云 API（待联调）",
        "unit": "周",
        "required_versions": ["sales_caliber", "inventory_caliber", "sku_mapping"],
    },
    {
        "code": "purchase_open_qty",
        "name": "在途采购量",
        "caliber": "采购状态、到货时间和关闭规则待业务确认",
        "source": "吉客云 API（待联调）",
        "unit": "台",
        "required_versions": ["sku_mapping", "warehouse_mapping"],
    },
]


def _pending(definition: Dict[str, Any]) -> Dict[str, Any]:
    return pending_metric(
        definition["code"],
        definition["name"],
        definition["caliber"],
        definition["unit"],
    )


class MetricsService:
    def __init__(self, review_service: ReviewService):
        self.review = review_service

    @staticmethod
    def dictionary() -> List[Dict[str, Any]]:
        return METRIC_DICTIONARY

    def formal_metrics(self, codes: Iterable[str]) -> Dict[str, Any]:
        definitions = {item["code"]: item for item in METRIC_DICTIONARY}
        selected = [definitions[code] for code in codes if code in definitions]
        required = sorted(
            {version for item in selected for version in item["required_versions"]}
        )
        gate = self.review.is_formal_eligible(required)
        # 本轮没有连接真实指标源，即使口径发布，也不得产生演示经营值。
        return {
            "mode": "formal",
            "data": [_pending(item) for item in selected],
            "gate": gate,
            "message": "待接入",
            "generated_business_data": False,
        }

    def sales_summary(self) -> Dict[str, Any]:
        return self.formal_metrics(("sales_amount", "paid_orders", "woi_28d"))

    def inventory_summary(self) -> Dict[str, Any]:
        return self.formal_metrics(("inventory_qty", "inventory_value", "woi_28d"))

    def purchase_summary(self) -> Dict[str, Any]:
        return self.formal_metrics(("purchase_open_qty",))

    def policy_summary(self) -> Dict[str, Any]:
        return {
            "mode": "formal",
            "data": [],
            "message": "待接入",
            "reason": "Apple 政策条款、期间、返点及适用范围尚未接入和确认",
            "generated_business_data": False,
        }
