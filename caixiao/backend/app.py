"""采销经营驾驶舱 HTTP 服务（Python 标准库，无外部依赖）。"""

import argparse
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from .adapters.demo import BUSINESS_UNITS, CHANNELS, DEMO_LABEL, DemoAdapter
from .adapters.jikexyun import JikexyunAdapter
from .adapters.snapshot import SnapshotAdapter
from .auth import issue_token, verify_password, verify_token
from .config import ROOT_DIR, Settings
from .database import Database
from .etl import (
    build_status_review,
    canonical_inventory_aging_record,
    canonical_inventory_fact,
    canonical_sales_fact,
    plan_sales_sync,
)
from .pipeline import recompute_five_time_views
from .sandbox import SANDBOX_LABEL, compare_inventory, compare_sales
from .models import ActionStatus
from .services.metrics import MetricsService
from .services.review import ReviewService


FRONTEND_DIR = ROOT_DIR / "caixiao" / "frontend"
COOKIE_NAME = "caixiao_session"
MAX_REQUEST_BYTES = 2 * 1024 * 1024
ALLOWED_ACTION_TYPES = [
    "补货", "暂停采购", "调拨", "分销", "价格清理", "活动",
    "搭售", "赠送", "退货", "报废", "继续观察",
]
ALLOWED_ACTION_STATUSES = [item.value for item in ActionStatus]


class DashboardApplication:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.database = Database(settings.db_path)
        self.database.bootstrap_admin(
            settings.bootstrap_user, settings.bootstrap_password
        )
        self.review = ReviewService(self.database)
        self.metrics = MetricsService(self.review, self.database)
        self.jky = JikexyunAdapter(settings.jky)
        self.demo = DemoAdapter() if settings.demo_mode else None
        self.snapshot = SnapshotAdapter(settings.sandbox_snapshot_dir)
        self.login_failures: Dict[str, Tuple[int, float]] = {}

    def close(self) -> None:
        self.database.close()

    def login_allowed(self, address: str) -> bool:
        attempts, blocked_until = self.login_failures.get(address, (0, 0.0))
        if blocked_until and time.time() < blocked_until:
            return False
        if blocked_until:
            self.login_failures.pop(address, None)
        return attempts < 5

    def login_failed(self, address: str) -> None:
        attempts, _ = self.login_failures.get(address, (0, 0.0))
        attempts += 1
        blocked_until = time.time() + 300 if attempts >= 5 else 0.0
        self.login_failures[address] = (attempts, blocked_until)

    def login_succeeded(self, address: str) -> None:
        self.login_failures.pop(address, None)


class DashboardServer(ThreadingHTTPServer):
    def __init__(self, address: Tuple[str, int], application: DashboardApplication):
        super().__init__(address, DashboardRequestHandler)
        self.application = application


class DashboardRequestHandler(BaseHTTPRequestHandler):
    server_version = "CaixiaoDashboard/0.1"

    @property
    def application(self) -> DashboardApplication:
        return self.server.application  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:
        # 日志不记录 Authorization、Cookie、请求体或外部凭据。
        print("{} - [{}] {}".format(self.client_address[0], self.log_date_time_string(), fmt % args))

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'",
        )
        self.send_header("Cache-Control", "no-store")
        origin = self.headers.get("Origin", "")
        if origin and origin in self.application.settings.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Credentials", "true")

    def _send_json(
        self,
        status: int,
        payload: Dict[str, Any],
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self._security_headers()
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, path: Path) -> None:
        if not path.is_file() or FRONTEND_DIR not in path.resolve().parents:
            self._send_json(404, {"error": "NOT_FOUND", "message": "资源不存在"})
            return
        content = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime + ("; charset=utf-8" if mime.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(content)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(content)

    def _read_json(self) -> Optional[Dict[str, Any]]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if length <= 0 or length > MAX_REQUEST_BYTES:
            return None
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            return payload if isinstance(payload, dict) else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _bearer_token(self) -> str:
        authorization = self.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            return authorization[7:].strip()
        raw_cookie = self.headers.get("Cookie", "")
        if raw_cookie:
            jar = cookies.SimpleCookie()
            try:
                jar.load(raw_cookie)
                if COOKIE_NAME in jar:
                    return jar[COOKIE_NAME].value
            except cookies.CookieError:
                pass
        return ""

    def _identity(self) -> Optional[Dict[str, Any]]:
        token = self._bearer_token()
        if not token:
            return None
        payload = verify_token(token, self.application.settings.token_secret)
        if not payload:
            return None
        if not self.application.database.session_active(
            payload["sid"], payload["sub"], int(time.time())
        ):
            return None
        user = self.application.database.get_user(payload["sub"])
        if not user:
            return None
        user["session_id"] = payload["sid"]
        return user

    def _require(self, scope: str) -> Optional[Dict[str, Any]]:
        identity = self._identity()
        if not identity:
            self._send_json(401, {"error": "UNAUTHORIZED", "message": "请先登录"})
            return None
        if scope not in identity["scopes"]:
            self._send_json(403, {"error": "FORBIDDEN", "message": "当前账号无此权限"})
            return None
        return identity

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin not in self.application.settings.allowed_origins:
            self._send_json(403, {"error": "ORIGIN_NOT_ALLOWED"})
            return
        self.send_response(204)
        self._security_headers()
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization,Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/cx/")
            self._security_headers()
            self.end_headers()
            return
        if path.startswith("/cx/assets/"):
            relative = unquote(path[len("/cx/") :])
            self._send_file(FRONTEND_DIR / relative)
            return
        if path == "/cx" or path.startswith("/cx/"):
            self._send_file(FRONTEND_DIR / "index.html")
            return
        if path == "/api/v1/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "caixiao-dashboard",
                    "version": "0.1.0",
                    "real_system_connected": False,
                    "demo_mode": self.application.settings.demo_mode,
                    "mode": "DEMO" if self.application.settings.demo_mode else "FORMAL",
                },
            )
            return
        if path == "/api/v1/auth/me":
            identity = self._require("dashboard:view")
            if identity:
                self._send_json(
                    200,
                    {
                        "username": identity["username"],
                        "role": identity["role"],
                        "scopes": identity["scopes"],
                        "data_scope": identity["data_scope"],
                    },
                )
            return
        if not path.startswith("/api/v1/"):
            self._send_json(404, {"error": "NOT_FOUND", "message": "接口不存在"})
            return
        if path.startswith("/api/v1/review/"):
            identity = self._require("review:view")
        elif path.startswith("/api/v1/sandbox/"):
            identity = self._require("sandbox:view")
        else:
            identity = self._require("dashboard:view")
        if not identity:
            return
        self._route_get(path, query, identity)

    def _route_get(
        self, path: str, query: Dict[str, Any], identity: Dict[str, Any]
    ) -> None:
        database = self.application.database
        review = self.application.review
        demo = self.application.demo
        filters = {name: query.get(name, [""])[0] for name in ("business_unit", "channel", "store", "start", "end", "compare")}
        if path == "/api/v1/system/context":
            if demo:
                self._send_json(200, demo.context())
            else:
                self._send_json(
                    200,
                    {
                        "mode": "formal", "data_class": "FORMAL", "label": "正式数据模式",
                        "banner": "", "demo_mode": False, "formal_kpi_enabled": True,
                        "real_system_connected": False, "generated_business_data": False,
                        "filters": {
                            "business_units": list(BUSINESS_UNITS), "channels": [], "stores": [],
                            "compare_modes": ["不对比", "环比/上一周期", "同比", "目标", "差额"],
                        },
                        "isolation": {
                            "FORMAL": "仅人工确认并发布后的真实事实、映射与口径可进入正式KPI",
                            "SANDBOX": "只用于差异验证，不进入正式KPI",
                            "DEMO": "关闭；正式模式绝不自动回退到演示数据",
                        },
                    },
                )
        elif path == "/api/v1/dim/boards":
            self._send_json(
                200,
                {
                    "data": DemoAdapter.boards(),
                    "source": "DEMO Adapter" if demo else "产品任务包",
                    "updated_at": None,
                    "conflict": False,
                    "data_class": "DEMO" if demo else "FORMAL",
                },
            )
        elif path == "/api/v1/dim/channels":
            self._send_json(200, {"data": demo.dimensions("channel_mapping") if demo else review.formal_dimensions("channel_mapping"), "gate": "DEMO_PUBLISHED" if demo else "PUBLISHED_ONLY", "data_class": "DEMO" if demo else "FORMAL"})
        elif path == "/api/v1/dim/warehouses":
            self._send_json(200, {"data": demo.dimensions("warehouse_mapping") if demo else review.formal_dimensions("warehouse_mapping"), "gate": "DEMO_PUBLISHED" if demo else "PUBLISHED_ONLY", "data_class": "DEMO" if demo else "FORMAL"})
        elif path == "/api/v1/dim/skus":
            self._send_json(200, {"data": demo.dimensions("sku_mapping") if demo else review.formal_dimensions("sku_mapping"), "gate": "DEMO_PUBLISHED" if demo else "PUBLISHED_ONLY", "data_class": "DEMO" if demo else "FORMAL"})
        elif path == "/api/v1/sales/summary":
            payload = demo.sales_summary(filters) if demo else self.application.metrics.sales_summary(filters=filters)
            payload["woi"] = demo.woi_summary(filters) if demo else self.application.metrics.woi_summary(filters=filters)
            self._send_json(200, payload)
        elif path == "/api/v1/sales/daily":
            payload = demo.sales_daily(filters) if demo else self.application.metrics.sales_daily(filters=filters)
            payload["date_range"] = {"start": query.get("start", [None])[0], "end": query.get("end", [None])[0]}
            self._send_json(200, payload)
        elif re.match(r"^/api/v1/sales/sku/[^/]+$", path):
            sku = unquote(path.rsplit("/", 1)[-1])
            payload = demo.sku_detail(sku, filters) if demo else self.application.metrics.sku_detail(sku, filters)
            payload["eligible_sku_count"] = len(demo.dimensions("sku_mapping") if demo else review.formal_dimensions("sku_mapping"))
            self._send_json(200, payload)
        elif path == "/api/v1/sales/status-review":
            rules = {
                item["source_key"]: str(item.get("value", {}).get("action", "PENDING"))
                for item in review.formal_dimensions("sales_adjustment_rules")
            }
            self._send_json(200, {"data": build_status_review(database.list_sales_facts(), rules), "adjustment_rules_published": bool(rules), "sales_caliber_published": bool(database.published_version("sales_caliber"))})
        elif path == "/api/v1/sync/sales/plan":
            state = database.get_sync_state("sales") or {}
            supports_modified = query.get("supports_modified", ["true"])[0].lower() != "false"
            try:
                lookback = int(query.get("lookback_days", ["7"])[0])
                payload = plan_sales_sync(state.get("cursor_value"), supports_modified=supports_modified, lookback_days=lookback)
            except (TypeError, ValueError) as exc:
                self._send_json(422, {"error": "SYNC_PLAN_VALIDATION", "message": str(exc)})
                return
            self._send_json(200, payload)
        elif path == "/api/v1/inventory/summary":
            self._send_json(200, demo.inventory_summary(filters) if demo else self.application.metrics.inventory_summary(filters=filters))
        elif path == "/api/v1/inventory/aging":
            self._send_json(200, demo.inventory_aging(filters) if demo else self.application.metrics.inventory_aging())
        elif path == "/api/v1/purchase/summary":
            self._send_json(200, demo.purchase_summary(filters) if demo else self.application.metrics.purchase_summary(filters=filters))
        elif path == "/api/v1/policy/summary":
            self._send_json(200, demo.policy_summary(filters) if demo else self.application.metrics.policy_summary())
        elif path == "/api/v1/anomaly/list":
            self._send_json(200, demo.anomaly_list(filters) if demo else self.application.metrics.anomaly_list())
        elif path == "/api/v1/action/list":
            status = query.get("status", [""])[0]
            if status and status not in ALLOWED_ACTION_STATUSES:
                self._send_json(422, {"error": "INVALID_ACTION_STATUS", "allowed": ALLOWED_ACTION_STATUSES})
                return
            if demo:
                payload = demo.action_list(filters)
                if status:
                    payload["data"] = [item for item in payload["data"] if item["status"] == status]
                payload["allowed_action_types"] = ALLOWED_ACTION_TYPES
                payload["allowed_statuses"] = ALLOWED_ACTION_STATUSES
                self._send_json(200, payload)
                return
            actions = database.list_actions(status)
            self._send_json(
                200,
                {
                    "data": actions,
                    "message": "已读取动作台账" if actions else "待接入",
                    "allowed_action_types": ALLOWED_ACTION_TYPES,
                    "allowed_statuses": ALLOWED_ACTION_STATUSES,
                    "approval_required": True,
                    "generated_business_data": False,
                },
            )
        elif path == "/api/v1/traffic/summary":
            if demo:
                self._send_json(200, demo.traffic_summary())
            else:
                self._send_json(200, {"data": [], "message": "待接入", "contract_fields": ["date", "store", "traffic", "source", "updated_at"], "formal_kpi_enabled": False, "real_system_connected": False, "generated_business_data": False, "data_class": "FORMAL"})
        elif path == "/api/v1/metrics/dict":
            self._send_json(200, {"data": self.application.metrics.dictionary()})
        elif path == "/api/v1/review/items":
            entity_type = query.get("entity_type", [""])[0]
            status = query.get("status", [""])[0]
            self._send_json(200, {"data": demo.review_items(entity_type, status) if demo else database.list_review_items(entity_type, status), "data_class": "DEMO" if demo else "FORMAL"})
        elif path == "/api/v1/review/versions":
            self._send_json(200, {"data": demo.versions() if demo else database.list_versions(), "data_class": "DEMO" if demo else "FORMAL"})
        elif path == "/api/v1/review/api-cards":
            self._send_json(200, {"data": demo.api_cards() if demo else self.application.jky.review_cards(), "data_class": "DEMO" if demo else "FORMAL", "label": DEMO_LABEL if demo else "正式接口配置复核"})
        elif path == "/api/v1/review/audit-log":
            self._send_json(200, {"data": database.audit_log()})
        elif path == "/api/v1/sandbox/compare":
            if demo:
                self._send_json(200, demo.sandbox_overview())
                return
            self._send_json(
                200,
                {
                    "mode": "sandbox",
                    "label": SANDBOX_LABEL,
                    "snapshot": self.application.snapshot.inspect(),
                    "formal": {
                        "message": "待接入",
                        "values_exposed": False,
                        "gate": review.is_formal_eligible(
                            (
                                "sales_caliber",
                                "inventory_caliber",
                                "warehouse_mapping",
                                "channel_mapping",
                                "sku_mapping",
                            )
                        ),
                    },
                    "isolation": "Sandbox 数据不得进入正式 KPI",
                },
            )
        else:
            self._send_json(404, {"error": "NOT_FOUND", "message": "接口不存在"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        if path == "/api/v1/auth/login":
            self._login()
            return
        if path == "/api/v1/auth/logout":
            identity = self._require("dashboard:view")
            if identity:
                self.application.database.revoke_session(identity["session_id"])
                self._send_json(
                    200,
                    {"status": "logged_out"},
                    {"Set-Cookie": COOKIE_NAME + "=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"},
                )
            return
        if path == "/api/v1/review/discover":
            identity = self._require("review:confirm")
            if identity:
                self._discover(identity)
            return
        if path == "/api/v1/review/confirm":
            identity = self._require("review:confirm")
            if identity:
                self._confirm(identity)
            return
        if path == "/api/v1/review/publish":
            identity = self._require("review:publish")
            if identity:
                self._publish(identity)
            return
        if path == "/api/v1/sandbox/recompute-times":
            identity = self._require("sandbox:view")
            if identity:
                self._recompute_times()
            return
        if path == "/api/v1/sandbox/compare":
            identity = self._require("sandbox:view")
            if identity:
                self._sandbox_compare()
            return
        if path == "/api/v1/facts/sales/upsert":
            identity = self._require("api:inspect")
            if identity:
                self._upsert_sales_facts(identity)
            return
        if path == "/api/v1/facts/inventory/upsert":
            identity = self._require("api:inspect")
            if identity:
                self._upsert_inventory_facts(identity)
            return
        if path == "/api/v1/facts/inventory-aging/upsert":
            identity = self._require("api:inspect")
            if identity:
                self._upsert_inventory_aging(identity)
            return
        if path == "/api/v1/actions/upsert":
            identity = self._require("review:confirm")
            if identity:
                self._upsert_action(identity)
            return
        self._send_json(404, {"error": "NOT_FOUND", "message": "接口不存在"})

    def _login(self) -> None:
        address = self.client_address[0]
        if not self.application.login_allowed(address):
            self._send_json(429, {"error": "TOO_MANY_ATTEMPTS", "message": "请稍后再试"})
            return
        body = self._read_json()
        if not body:
            self._send_json(400, {"error": "INVALID_JSON"})
            return
        username = str(body.get("username", ""))
        password = str(body.get("password", ""))
        user = self.application.database.get_user(username)
        if not user or not verify_password(password, user["password_hash"]):
            self.application.login_failed(address)
            self._send_json(401, {"error": "INVALID_CREDENTIALS", "message": "账号或密码错误"})
            return
        self.application.login_succeeded(address)
        token, payload = issue_token(
            username,
            self.application.settings.token_secret,
            self.application.settings.session_ttl_seconds,
        )
        self.application.database.save_session(payload["sid"], username, payload["exp"])
        cookie_value = "{}={}; Path=/; HttpOnly; SameSite=Strict; Max-Age={}".format(
            COOKIE_NAME, token, self.application.settings.session_ttl_seconds
        )
        self._send_json(
            200,
            {"status": "authenticated", "username": username, "expires_at": payload["exp"]},
            {"Set-Cookie": cookie_value},
        )

    def _discover(self, identity: Dict[str, Any]) -> None:
        if self.application.demo:
            self._send_json(409, {"error": "DEMO_ISOLATION", "message": "Demo模式不写入正式复核库；请使用预置演示复核对象"})
            return
        body = self._read_json()
        if not body:
            self._send_json(400, {"error": "INVALID_JSON"})
            return
        raw_code = str(body.get("raw_code") or body.get("source_key") or "").strip()
        source_key = str(body.get("source_key") or raw_code).strip()
        raw_value = body.get("raw_value", {})
        raw_name = str(body.get("raw_name") or (raw_value.get("name") if isinstance(raw_value, dict) else "") or "").strip()
        required = ("entity_type", "source_system", "raw_code", "raw_name")
        if not body.get("entity_type") or not body.get("source_system") or not raw_code or not raw_name:
            self._send_json(422, {"error": "MISSING_FIELD", "required": list(required)})
            return
        if body["entity_type"] not in {
            "sales_caliber",
            "inventory_caliber",
            "warehouse_mapping",
            "channel_mapping",
            "sku_mapping",
            "sales_adjustment_rules",
            "anomaly_thresholds",
        }:
            self._send_json(422, {"error": "INVALID_ENTITY_TYPE"})
            return
        if not isinstance(raw_value, dict) or not isinstance(body.get("suggestion", {}), dict):
            self._send_json(422, {"error": "INVALID_VALUE"})
            return
        try:
            item_id = self.application.database.upsert_review_item(
                body["entity_type"], str(body["source_system"]), source_key,
                raw_value, body.get("suggestion", {}), body.get("confidence"),
                raw_code=raw_code, raw_name=raw_name,
                history_mapping=body.get("history_mapping", []),
                suggested_display_name=str(body.get("suggested_display_name") or ""),
            )
        except (ValueError, TypeError) as exc:
            self._send_json(422, {"error": "IMMUTABLE_RAW_FIELDS", "message": str(exc)})
            return
        self.application.database.audit(
            identity["username"],
            "review.discover",
            "review_item",
            str(item_id),
            {"entity_type": body["entity_type"], "source_system": body["source_system"]},
        )
        item = next(value for value in self.application.database.list_review_items() if value["id"] == item_id)
        self._send_json(201, {**item, "formal_kpi_enabled": False})

    def _confirm(self, identity: Dict[str, Any]) -> None:
        body = self._read_json()
        if not body:
            self._send_json(400, {"error": "INVALID_JSON"})
            return
        forbidden = {"raw_code", "raw_name", "history_mapping", "raw_value", "source_key"}
        if forbidden.intersection(body) or any(forbidden.intersection(item) for item in body.get("decisions", []) if isinstance(item, dict)):
            self._send_json(422, {"error": "RAW_FIELDS_READ_ONLY", "message": "raw_code、raw_name 和 history_mapping 永久只读"})
            return
        if bool(body.get("publish", False)) and "review:publish" not in identity["scopes"]:
            self._send_json(403, {"error": "FORBIDDEN", "message": "当前账号无版本发布权限"})
            return
        try:
            result = self.application.demo.confirm(body, identity["username"]) if self.application.demo else self.application.review.confirm(
                str(body.get("version_type", "")), str(body.get("version_name", "")), body.get("item_ids", []),
                identity["username"], bool(body.get("publish", False)), str(body.get("reason", "")),
                body.get("affected_metrics", []), body.get("decisions", []),
            )
        except (ValueError, TypeError) as exc:
            self._send_json(422, {"error": "REVIEW_VALIDATION", "message": str(exc)})
            return
        self._send_json(201, result)

    def _publish(self, identity: Dict[str, Any]) -> None:
        body = self._read_json()
        if not body:
            self._send_json(400, {"error": "INVALID_JSON"})
            return
        try:
            result = self.application.demo.publish(int(body.get("version_id", 0)), identity["username"]) if self.application.demo else self.application.review.publish(int(body.get("version_id", 0)), identity["username"])
        except (ValueError, TypeError) as exc:
            self._send_json(422, {"error": "PUBLISH_VALIDATION", "message": str(exc)})
            return
        self._send_json(200, result)

    def _recompute_times(self) -> None:
        body = self._read_json()
        if not body or not isinstance(body.get("records"), list):
            self._send_json(400, {"error": "INVALID_JSON", "message": "records 必须是数组"})
            return
        if len(body["records"]) > 5000:
            self._send_json(413, {"error": "TOO_MANY_RECORDS"})
            return
        amount_field = str(body.get("amount_field", "amount"))
        self._send_json(
            200,
            {
                "mode": "sandbox",
                "label": SANDBOX_LABEL,
                "views": recompute_five_time_views(body["records"], amount_field),
                "formal_kpi_enabled": False,
            },
        )

    def _sandbox_compare(self) -> None:
        body = self._read_json()
        if not body or not isinstance(body.get("old_records"), list) or not isinstance(body.get("new_records"), list):
            self._send_json(400, {"error": "INVALID_JSON", "message": "old_records 和 new_records 必须是数组"})
            return
        if len(body["old_records"]) + len(body["new_records"]) > 10000:
            self._send_json(413, {"error": "TOO_MANY_RECORDS"})
            return
        domain = str(body.get("domain", ""))
        try:
            result = compare_sales(body["old_records"], body["new_records"]) if domain == "sales" else compare_inventory(body["old_records"], body["new_records"]) if domain == "inventory" else None
        except (TypeError, ValueError) as exc:
            self._send_json(422, {"error": "COMPARE_VALIDATION", "message": str(exc)})
            return
        if result is None:
            self._send_json(422, {"error": "INVALID_DOMAIN", "allowed": ["sales", "inventory"]})
            return
        self._send_json(200, result)

    def _upsert_sales_facts(self, identity: Dict[str, Any]) -> None:
        if self.application.demo:
            self._send_json(409, {"error": "DEMO_ISOLATION", "message": "Demo模式禁止写入正式销售事实"})
            return
        body = self._read_json()
        if not body or not isinstance(body.get("records"), list) or not isinstance(body.get("field_mapping"), dict):
            self._send_json(400, {"error": "INVALID_JSON", "message": "records 和 field_mapping 必填"})
            return
        try:
            records = [canonical_sales_fact(raw, body["field_mapping"], body.get("metadata", {})) for raw in body["records"]]
            count = self.application.database.upsert_sales_facts(records)
        except (TypeError, ValueError) as exc:
            self._send_json(422, {"error": "FACT_VALIDATION", "message": str(exc)})
            return
        self.application.database.audit(identity["username"], "facts.upsert", "sales", None, {"record_count": count, "sync_job_id": body.get("metadata", {}).get("sync_job_id")})
        self._send_json(200, {"upserted": count, "formal_kpi_enabled": False, "message": "事实已入库；仍须通过映射和口径发布门禁"})

    def _upsert_inventory_facts(self, identity: Dict[str, Any]) -> None:
        if self.application.demo:
            self._send_json(409, {"error": "DEMO_ISOLATION", "message": "Demo模式禁止写入正式库存事实"})
            return
        body = self._read_json()
        if not body or not isinstance(body.get("records"), list) or not isinstance(body.get("field_mapping"), dict):
            self._send_json(400, {"error": "INVALID_JSON", "message": "records 和 field_mapping 必填"})
            return
        try:
            records = [canonical_inventory_fact(raw, body["field_mapping"], body.get("metadata", {})) for raw in body["records"]]
            count = self.application.database.upsert_inventory_facts(records)
        except (TypeError, ValueError) as exc:
            self._send_json(422, {"error": "FACT_VALIDATION", "message": str(exc)})
            return
        self.application.database.audit(identity["username"], "facts.upsert", "inventory", None, {"record_count": count, "sync_job_id": body.get("metadata", {}).get("sync_job_id")})
        self._send_json(200, {"upserted": count, "formal_kpi_enabled": False, "message": "事实已入库；仍须通过映射和口径发布门禁"})

    def _upsert_inventory_aging(self, identity: Dict[str, Any]) -> None:
        if self.application.demo:
            self._send_json(409, {"error": "DEMO_ISOLATION", "message": "Demo模式禁止写入正式库龄事实"})
            return
        body = self._read_json()
        if not body or not isinstance(body.get("records"), list):
            self._send_json(400, {"error": "INVALID_JSON", "message": "records 必须是数组"})
            return
        try:
            records = [canonical_inventory_aging_record(raw, body.get("metadata", {})) for raw in body["records"]]
            count = self.application.database.upsert_inventory_aging_records(records)
        except (TypeError, ValueError) as exc:
            self._send_json(422, {"error": "AGING_VALIDATION", "message": str(exc)})
            return
        self.application.database.audit(identity["username"], "facts.upsert", "inventory_aging", None, {"record_count": count, "sync_job_id": body.get("metadata", {}).get("sync_job_id")})
        self._send_json(200, {"upserted": count, "formal_kpi_enabled": False, "message": "库龄结构已入库；确认状态及映射发布通过后方可展示正式数值"})

    def _upsert_action(self, identity: Dict[str, Any]) -> None:
        if self.application.demo:
            self._send_json(409, {"error": "DEMO_ISOLATION", "message": "Demo模式不写入正式动作台账"})
            return
        body = self._read_json()
        required = ("action_code", "action_type", "title", "status")
        if not body or any(not body.get(field) for field in required):
            self._send_json(422, {"error": "MISSING_FIELD", "required": list(required)})
            return
        if body["action_type"] not in ALLOWED_ACTION_TYPES or body["status"] not in ALLOWED_ACTION_STATUSES:
            self._send_json(422, {"error": "ACTION_VALIDATION", "allowed_action_types": ALLOWED_ACTION_TYPES, "allowed_statuses": ALLOWED_ACTION_STATUSES})
            return
        record = {key: str(body.get(key) or "").strip() for key in (
            "action_code", "action_type", "title", "status", "business_unit", "channel",
            "store_shop", "sku", "source_reference", "reason",
        )}
        record["created_by"] = identity["username"]
        action_id = self.application.database.upsert_action(record)
        self.application.database.audit(identity["username"], "action.upsert", "action_ledger", str(action_id), {"action_code": record["action_code"], "status": record["status"]})
        self._send_json(200, {"id": action_id, "status": record["status"]})


def create_server(settings: Settings) -> DashboardServer:
    settings.validate_for_server()
    application = DashboardApplication(settings)
    return DashboardServer((settings.host, settings.port), application)


def main() -> None:
    parser = argparse.ArgumentParser(description="采销经营驾驶舱")
    parser.add_argument("--check", action="store_true", help="仅检查配置和数据库初始化")
    args = parser.parse_args()
    settings = Settings.from_env()
    server = create_server(settings)
    if args.check:
        server.server_close()
        server.application.close()
        print("配置检查通过")
        return
    print("采销经营驾驶舱已启动：http://{}:{}/cx/".format(settings.host, settings.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.application.close()


if __name__ == "__main__":
    main()
