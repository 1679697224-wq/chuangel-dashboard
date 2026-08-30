"""吉客云适配层。未配置真实端点和凭据时严格禁用。"""

import json
from typing import Any, Dict, Mapping
from urllib import request


DOMAINS = ("sales", "inventory", "purchase", "transfer")
SALES_REQUIRED_FACT_FIELDS = (
    "trade_no", "line_id", "create_time", "pay_time", "audit_time",
    "consign_time", "complete_time", "modified_time", "trade_status",
    "quantity", "payment", "warehouse", "shop/channel", "goods_no", "sku",
    "source_api", "raw_json_reference",
)


class JikexyunAdapter:
    def __init__(self, config: Mapping[str, str]):
        self.config = dict(config)

    def review_cards(self):
        cards = []
        for domain in DOMAINS:
            endpoint = self.config.get(domain + "_endpoint", "")
            missing = []
            if not self.config.get("base_url"):
                missing.append("base_url")
            if not endpoint:
                missing.append(domain + "_endpoint")
            if not self.config.get("app_key"):
                missing.append("app_key")
            if not self.config.get("app_secret") and not self.config.get("access_token"):
                missing.append("credential")
            cards.append(
                {
                    "domain": domain,
                    "name": {
                        "sales": "销售 API",
                        "inventory": "库存 API",
                        "purchase": "采购 API",
                        "transfer": "调拨 API",
                    }[domain],
                    "status": "待确认" if missing else "待联调",
                    "configured": not missing,
                    "missing": missing,
                    "endpoint": "已配置" if endpoint else "待接入",
                    "pipeline": ["原始API数据", "清洗", "映射", "指标计算"],
                    "formal_kpi_enabled": False,
                    "sync_strategy": (
                        {
                            "preferred_cursor": "modified_time 或等同订单更新时间",
                            "fallback": "滚动回溯窗口 + (source_system, trade_no, line_id) upsert",
                            "prohibited_scope": "不得以 consign_time 窗口决定付款销售事实入库",
                            "required_fact_fields": list(SALES_REQUIRED_FACT_FIELDS),
                            "confirmation": "接口字段、分页、限流和 modified 稳定性待 WorkBuddy/PO 联调确认",
                        }
                        if domain == "sales" else None
                    ),
                }
            )
        return cards

    def fetch(self, domain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if domain not in DOMAINS:
            raise ValueError("不支持的吉客云数据域")
        cards = {card["domain"]: card for card in self.review_cards()}
        if not cards[domain]["configured"]:
            raise RuntimeError("吉客云接口或凭据未配置，禁止伪造返回结果")
        endpoint = self.config["base_url"].rstrip("/") + "/" + self.config[
            domain + "_endpoint"
        ].lstrip("/")
        headers = {"Content-Type": "application/json", "X-App-Key": self.config["app_key"]}
        if self.config.get("access_token"):
            headers["Authorization"] = "Bearer " + self.config["access_token"]
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        api_request = request.Request(endpoint, data=body, headers=headers, method="POST")
        with request.urlopen(api_request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
