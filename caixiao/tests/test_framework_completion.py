import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

from caixiao.backend.app import create_server
from caixiao.backend.config import Settings


REPO_ROOT = Path(__file__).resolve().parents[2]


class DemoModeApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.settings = Settings(
            host="127.0.0.1", port=0, db_path=Path(cls.temp.name) / "demo.sqlite3",
            allowed_origins=("http://127.0.0.1",), token_secret="demo-test-secret-" * 3,
            bootstrap_user="demo-admin", bootstrap_password="demo-password-123",
            session_ttl_seconds=600, sandbox_snapshot_dir="", jky={}, demo_mode=True,
        )
        cls.server = create_server(cls.settings)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server.application.close()
        cls.thread.join(timeout=3)
        cls.temp.cleanup()

    def request(self, method, path, body=None, cookie=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=4)
        headers = {}
        encoded = None
        if body is not None:
            encoded = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if cookie:
            headers["Cookie"] = cookie
        connection.request(method, path, body=encoded, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        payload = json.loads(raw.decode("utf-8")) if raw else {}
        result = response.status, dict(response.getheaders()), payload
        connection.close()
        return result

    def login(self):
        status, headers, _ = self.request(
            "POST", "/api/v1/auth/login",
            {"username": "demo-admin", "password": "demo-password-123"},
        )
        self.assertEqual(status, 200)
        return headers["Set-Cookie"].split(";", 1)[0]

    def test_demo_context_is_explicit_and_not_formal(self):
        cookie = self.login()
        status, _, body = self.request("GET", "/api/v1/system/context", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertTrue(body["demo_mode"])
        self.assertEqual(body["data_class"], "DEMO")
        self.assertEqual(body["banner"], "演示数据，仅用于页面及流程验证")
        self.assertFalse(body["formal_kpi_enabled"])
        self.assertFalse(body["real_system_connected"])

    def test_demo_business_endpoints_are_labelled_and_nonempty(self):
        cookie = self.login()
        endpoints = (
            "/api/v1/sales/summary", "/api/v1/sales/daily",
            "/api/v1/sales/sku/DEMO-APL-PH-001", "/api/v1/inventory/summary",
            "/api/v1/inventory/aging", "/api/v1/purchase/summary",
            "/api/v1/policy/summary", "/api/v1/anomaly/list",
            "/api/v1/action/list", "/api/v1/traffic/summary",
        )
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                status, _, body = self.request("GET", endpoint, cookie=cookie)
                self.assertEqual(status, 200)
                self.assertEqual(body["data_class"], "DEMO")
                self.assertFalse(body["formal_kpi_enabled"])
                self.assertFalse(body["real_system_connected"])
                self.assertEqual(body["label"], "演示数据，仅用于页面及流程验证")

    def test_seven_business_scopes_change_sales_and_inventory_together(self):
        cookie = self.login()
        scopes = (
            ("Apple线下", "APR"), ("Apple线下", "即时零售"),
            ("Apple电商", "京东"), ("Apple电商", "苏宁"),
            ("舒尔电商", "天猫"), ("舒尔电商", "京东"),
            ("分销渠道", "分销"),
        )
        results = []
        for business_unit, channel in scopes:
            query = urlencode({"business_unit": business_unit, "channel": channel})
            _, _, sales = self.request("GET", "/api/v1/sales/summary?" + query, cookie=cookie)
            _, _, inventory = self.request("GET", "/api/v1/inventory/summary?" + query, cookie=cookie)
            sales_amount = next(item["value"] for item in sales["data"] if item["code"] == "sales_amount")
            inventory_amount = next(item["value"] for item in inventory["data"] if item["code"] == "operating_inventory_amount")
            self.assertIn(business_unit, sales["scope"])
            self.assertIn(channel, inventory["scope"])
            results.append((sales_amount, inventory_amount))
        self.assertEqual(len(set(results)), len(scopes))

    def test_demo_review_is_in_memory_and_raw_fields_stay_read_only(self):
        cookie = self.login()
        _, _, items = self.request("GET", "/api/v1/review/items", cookie=cookie)
        item = next(value for value in items["data"] if value["status"] == "UNCONFIRMED")
        status, _, body = self.request("POST", "/api/v1/review/confirm", {
            "version_type": item["entity_type"], "version_name": "demo_review_test_v1",
            "item_ids": [item["id"]], "raw_name": "不得修改", "reason": "非法字段测试",
        }, cookie)
        self.assertEqual(status, 422)
        self.assertEqual(body["error"], "RAW_FIELDS_READ_ONLY")
        status, _, version = self.request("POST", "/api/v1/review/confirm", {
            "version_type": item["entity_type"], "version_name": "demo_review_test_v1",
            "item_ids": [item["id"]],
            "decisions": [{"item_id": item["id"], "display_name": "人工确认演示名"}],
            "publish": True, "reason": "验证演示确认与发布", "affected_metrics": ["demo_metric"],
        }, cookie)
        self.assertEqual(status, 201)
        self.assertEqual(version["status"], "PUBLISHED")
        self.assertEqual(self.server.application.database.list_review_items(), [])

    def test_demo_cannot_write_formal_facts_or_action_ledger(self):
        cookie = self.login()
        for endpoint, body in (
            ("/api/v1/facts/sales/upsert", {"records": [], "field_mapping": {}}),
            ("/api/v1/facts/inventory/upsert", {"records": [], "field_mapping": {}}),
            ("/api/v1/facts/inventory-aging/upsert", {"records": []}),
            ("/api/v1/actions/upsert", {"action_code": "DEMO", "action_type": "补货", "title": "演示", "status": "待确认"}),
            ("/api/v1/review/discover", {"entity_type": "sku_mapping"}),
        ):
            with self.subTest(endpoint=endpoint):
                status, _, result = self.request("POST", endpoint, body, cookie)
                self.assertEqual(status, 409)
                self.assertEqual(result["error"], "DEMO_ISOLATION")

    def test_sandbox_remains_separate_from_demo_and_formal(self):
        cookie = self.login()
        status, _, body = self.request("GET", "/api/v1/sandbox/compare", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(body["data_class"], "SANDBOX")
        self.assertIn("不代表正式经营口径", body["label"])
        self.assertFalse(body["formal_kpi_enabled"])

    def test_business_and_admin_page_routes_are_available(self):
        for path in (
            "/cx/", "/cx/anomalies", "/cx/priorities", "/cx/products", "/cx/sku",
            "/cx/inventory", "/cx/purchase", "/cx/transfer", "/cx/policy/dg",
            "/cx/policy/subsidy", "/cx/policy", "/cx/actions", "/cx/actions/tracking",
            "/cx/admin/data-mapping", "/cx/admin/connectors/jikexyun",
            "/cx/admin/validation/sandbox",
        ):
            with self.subTest(path=path):
                connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=4)
                connection.request("GET", path)
                response = connection.getresponse()
                html = response.read().decode("utf-8")
                connection.close()
                self.assertEqual(response.status, 200)
                self.assertIn("采销经营驾驶舱", html)


class FrameworkSourceTests(unittest.TestCase):
    def test_demo_flag_parsing_is_exact(self):
        with patch.dict("os.environ", {"DEMO_MODE": "true"}, clear=True):
            self.assertTrue(Settings.from_env().demo_mode)
        with patch.dict("os.environ", {"DEMO_MODE": "false"}, clear=True):
            self.assertFalse(Settings.from_env().demo_mode)
        with patch.dict("os.environ", {"DEMO_MODE": "sometimes"}, clear=True):
            with self.assertRaises(ValueError):
                Settings.from_env()

    def test_frontend_contains_required_complete_framework(self):
        source = (REPO_ROOT / "caixiao/frontend/assets/app.js").read_text(encoding="utf-8")
        index = (REPO_ROOT / "caixiao/frontend/index.html").read_text(encoding="utf-8")
        for phrase in (
            "当前为模拟数据，仅用于页面和交互验证", "DG SI", "DG ST", "单店补贴",
            "现货WOI", "含在途WOI", "7/14/28/90", "date / store / traffic / source / updated_at",
            "验证数据，不代表正式经营口径", "raw_code、raw_name、history_mapping永久只读",
        ):
            self.assertIn(phrase, source + index)

    def test_formal_mode_has_no_automatic_demo_fallback(self):
        source = (REPO_ROOT / "caixiao/backend/app.py").read_text(encoding="utf-8")
        self.assertIn("DemoAdapter() if settings.demo_mode else None", source)
        self.assertNotIn("if not payload: demo", source)


if __name__ == "__main__":
    unittest.main()
