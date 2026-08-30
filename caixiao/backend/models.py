"""稳定的数据合同与枚举。"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ReviewStatus(str, Enum):
    UNCONFIRMED = "UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class VersionStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"


class DataMode(str, Enum):
    FORMAL = "formal"
    SANDBOX = "sandbox"


class AdjustmentAction(str, Enum):
    """销售调整动作。最终状态归类必须由人工发布版本决定。"""

    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"
    OFFSET = "OFFSET"
    PENDING = "PENDING"


class InventoryClass(str, Enum):
    """经营库存的三种可配置归类。"""

    SPOT = "SPOT"
    IN_TRANSIT = "IN_TRANSIT"
    EXCLUDE = "EXCLUDE"


VERSION_PREFIXES = {
    "sales_caliber": "sales_caliber_v",
    "inventory_caliber": "inventory_caliber_v",
    "warehouse_mapping": "warehouse_mapping_v",
    "channel_mapping": "channel_mapping_v",
    "sku_mapping": "sku_mapping_v",
    "sales_adjustment_rules": "sales_adjustment_rules_v",
}


@dataclass(frozen=True)
class MetricValue:
    code: str
    name: str
    value: Optional[Any]
    caliber: str
    source: str
    updated_at: Optional[str]
    conflict: bool
    unit: str
    status: str = "待接入"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "value": self.value,
            "caliber": self.caliber,
            "source": self.source,
            "updated_at": self.updated_at,
            "conflict": self.conflict,
            "unit": self.unit,
            "status": self.status,
        }


def pending_metric(code: str, name: str, caliber: str, unit: str) -> Dict[str, Any]:
    return MetricValue(
        code=code,
        name=name,
        value=None,
        caliber=caliber,
        source="未接入",
        updated_at=None,
        conflict=False,
        unit=unit,
    ).as_dict()
