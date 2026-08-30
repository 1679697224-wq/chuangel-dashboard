import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from caixiao.backend.app import create_server
from caixiao.backend.config import Settings


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.settings = Settings(
            host="127.0.0.1", port=0, db_path=Path(cls.temp.name) / "api.sqlite3",
            allowed_origins=("http://127.0.0.1",), token_secret="test-secret-" * 4,
            bootstrap_user="review-admin", bootstrap_password="test-password-123",
            session_ttl_seconds=600, sandbox_snapshot_dir="", jky={},
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

    def request(self, method, path, body=None, cookie=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=4)
        request_headers = dict(headers or {})
        encoded = None
        if body is not None:
            encoded = json.dumps(body).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        if cookie:
            request_headers["Cookie"] = cookie
        connection.request(method, path, body=encoded, headers=request_headers)
        response = connection.getresponse()
        raw = response.read()
        data = json.loads(raw.decode("utf-8")) if raw else {}
        result = (response.status, dict(response.getheaders()), data)
        connection.close()
        return result

    def login(self):
        status, headers, _ = self.request("POST", "/api/v1/auth/login", {"username":"review-admin","password":"test-password-123"})
        self.assertEqual(status, 200)
        return headers["Set-Cookie"].split(";", 1)[0]

    def test_health_public(self):
        status, _, body = self.request("GET", "/api/v1/health")
        self.assertEqual(status, 200)
        self.assertFalse(body["real_system_connected"])

    def test_api_requires_authentication(self):
        status, _, body = self.request("GET", "/api/v1/sales/summary")
        self.assertEqual(status, 401)
        self.assertEqual(body["error"], "UNAUTHORIZED")

    def test_four_business_pages_are_accessible(self):
        for path in ("/cx/", "/cx/sku", "/cx/inventory-purchase", "/cx/apple-policy"):
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=4)
            connection.request("GET", path)
            response = connection.getresponse()
            content = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("采销经营驾驶舱", content)
            connection.close()

    def test_formal_metrics_are_pending_not_fake(self):
        cookie = self.login()
        status, _, body = self.request("GET", "/api/v1/sales/summary", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertFalse(body["generated_business_data"])
        self.assertTrue(all(metric["value"] is None for metric in body["data"]))
        self.assertTrue(all(metric["status"] == "待确认" for metric in body["data"]))
        for metric in body["data"]:
            self.assertTrue({"value","caliber","source","updated_at","conflict","unit"}.issubset(metric))

    def test_review_draft_cannot_enter_formal_dimension(self):
        cookie = self.login()
        status, _, discovered = self.request("POST", "/api/v1/review/discover", {
            "entity_type":"channel_mapping","source_system":"test","source_key":"channel-a",
            "raw_value":{"name":"source-a"},"suggestion":{"canonical":"channel-a"},"confidence":0.9
        }, cookie)
        self.assertEqual(status, 201)
        status, _, _ = self.request("POST", "/api/v1/review/confirm", {
            "version_type":"channel_mapping","version_name":"channel_mapping_v1","item_ids":[discovered["id"]],"publish":False,
            "reason":"测试确认","affected_metrics":["sales_amount"]
        }, cookie)
        self.assertEqual(status, 201)
        _, _, dimensions = self.request("GET", "/api/v1/dim/channels", cookie=cookie)
        self.assertEqual(dimensions["data"], [])

    def test_published_version_enters_formal_dimension(self):
        cookie = self.login()
        status, _, discovered = self.request("POST", "/api/v1/review/discover", {
            "entity_type":"sku_mapping","source_system":"test","source_key":"sku-a",
            "raw_value":{"name":"source-sku"},"suggestion":{"canonical":"sku-a"}
        }, cookie)
        self.assertEqual(status, 201)
        status, _, version = self.request("POST", "/api/v1/review/confirm", {
            "version_type":"sku_mapping","version_name":"sku_mapping_v1","item_ids":[discovered["id"]],"publish":False,
            "reason":"测试确认","affected_metrics":["sales_amount"]
        }, cookie)
        self.assertEqual(status, 201)
        status, _, published = self.request("POST", "/api/v1/review/publish", {"version_id":version["id"]}, cookie)
        self.assertEqual(status, 200)
        self.assertEqual(published["status"], "PUBLISHED")
        _, _, dimensions = self.request("GET", "/api/v1/dim/skus", cookie=cookie)
        self.assertEqual(len(dimensions["data"]), 1)

    def test_sandbox_is_explicitly_isolated(self):
        cookie = self.login()
        status, _, body = self.request("GET", "/api/v1/sandbox/compare", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(body["mode"], "sandbox")
        self.assertIn("不得进入正式 KPI", body["isolation"])

    def test_five_time_recompute_endpoint(self):
        cookie = self.login()
        record = {key:"2026-08-01" for key in ("create_time","pay_time","audit_time","consign_time","complete_time")}
        record["amount"] = 10
        status, _, body = self.request("POST", "/api/v1/sandbox/recompute-times", {"records":[record],"amount_field":"amount"}, cookie)
        self.assertEqual(status, 200)
        self.assertEqual(len(body["views"]), 5)
        self.assertFalse(body["formal_kpi_enabled"])

    def test_sandbox_sales_difference_endpoint(self):
        cookie = self.login()
        status, _, body = self.request("POST", "/api/v1/sandbox/compare", {
            "domain":"sales",
            "old_records":[{"trade_no":"A","amount":100,"channel_raw_name":"C","store_raw_name":"S","sku_raw":"K"}],
            "new_records":[{"trade_no":"A","payment":90,"pay_time":"2026-08-01","channel_raw_name":"C","store_raw_name":"S","sku_raw":"K"}],
        }, cookie)
        self.assertEqual(status, 200)
        self.assertEqual(body["difference"], -10)
        self.assertEqual(body["label"], "验证数据，不代表正式经营口径")
        self.assertFalse(body["formal_kpi_enabled"])

    def test_fact_upsert_remains_behind_formal_gate(self):
        cookie = self.login()
        raw = {
            "trade_no":"API-T1","line_id":"L1","create_time":"2026-07-31T22:00:00",
            "pay_time":"2026-07-31T23:00:00","audit_time":"2026-08-01T00:00:00",
            "consign_time":"2026-08-03T12:00:00","complete_time":"2026-08-05T00:00:00",
            "modified_time":"2026-08-05T01:00:00","trade_status":"待审核","quantity":1,"payment":100,
            "warehouse_raw_name":"WH-API","channel_raw_name":"CH-API","store_raw_name":"STORE-API",
            "goods_no":"G-API","sku_raw":"SKU-API","source_api":"orders.modified",
            "raw_json_reference":"blob://sales/API-T1/L1"
        }
        metadata = {"source_system":"jikexyun","source_record_id":"API-R1","extracted_at":"2026-08-05T01:01:00Z","synced_at":"2026-08-05T01:02:00Z","sync_job_id":"API-JOB1"}
        status, _, body = self.request("POST", "/api/v1/facts/sales/upsert", {"records":[raw],"field_mapping":{},"metadata":metadata}, cookie)
        self.assertEqual(status, 200)
        self.assertEqual(body["upserted"], 1)
        self.assertFalse(body["formal_kpi_enabled"])
        _, _, summary = self.request("GET", "/api/v1/sales/summary", cookie=cookie)
        self.assertFalse(summary["gate"]["eligible"])
        self.assertTrue(all(item["value"] is None for item in summary["data"]))
        _, _, statuses = self.request("GET", "/api/v1/sales/status-review", cookie=cookie)
        self.assertTrue(any(item["raw_trade_status"] == "待审核" for item in statuses["data"]))

    def test_origin_not_allowlisted_for_preflight(self):
        status, headers, _ = self.request("OPTIONS", "/api/v1/sales/summary", headers={"Origin":"https://not-allowed.example"})
        self.assertEqual(status, 403)
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_api_review_cards_have_no_fake_payload(self):
        cookie = self.login()
        status, _, body = self.request("GET", "/api/v1/review/api-cards", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(len(body["data"]), 4)
        self.assertTrue(all(not card["formal_kpi_enabled"] for card in body["data"]))

    def test_required_get_endpoints_contract(self):
        cookie = self.login()
        endpoints = (
            "/api/v1/dim/boards", "/api/v1/dim/channels", "/api/v1/dim/warehouses",
            "/api/v1/dim/skus", "/api/v1/sales/summary", "/api/v1/sales/daily",
            "/api/v1/sales/sku/UNSELECTED", "/api/v1/inventory/summary",
            "/api/v1/inventory/aging", "/api/v1/purchase/summary",
            "/api/v1/policy/summary", "/api/v1/anomaly/list", "/api/v1/action/list",
            "/api/v1/sandbox/compare", "/api/v1/metrics/dict",
            "/api/v1/review/items", "/api/v1/review/versions",
            "/api/v1/review/api-cards", "/api/v1/review/audit-log",
            "/api/v1/sales/status-review", "/api/v1/sync/sales/plan",
        )
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                status, _, body = self.request("GET", endpoint, cookie=cookie)
                self.assertEqual(status, 200)
                self.assertIsInstance(body, dict)

    def test_action_vocabulary_is_closed_and_requires_approval(self):
        cookie = self.login()
        status, _, body = self.request("GET", "/api/v1/action/list", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertTrue(body["approval_required"])
        self.assertEqual(
            body["allowed_action_types"],
            ["补货", "暂停采购", "调拨", "分销", "价格清理", "活动", "搭售", "赠送", "退货", "报废", "继续观察"],
        )

    def test_review_api_rejects_raw_field_modification(self):
        cookie = self.login()
        status, _, item = self.request("POST", "/api/v1/review/discover", {
            "entity_type":"channel_mapping", "source_system":"round2",
            "raw_code":"RAW-LOCKED", "raw_name":"原始名称",
            "history_mapping":[], "suggested_display_name":"建议展示名",
            "raw_value":{}, "suggestion":{"canonical":"建议展示名"},
        }, cookie)
        self.assertEqual(status, 201)
        status, _, body = self.request("POST", "/api/v1/review/discover", {
            "entity_type":"channel_mapping", "source_system":"round2",
            "raw_code":"RAW-LOCKED", "raw_name":"试图修改",
            "history_mapping":[], "raw_value":{}, "suggestion":{},
        }, cookie)
        self.assertEqual(status, 422)
        self.assertEqual(body["error"], "IMMUTABLE_RAW_FIELDS")
        status, _, _ = self.request("POST", "/api/v1/review/discover", {
            "entity_type":"warehouse_mapping", "source_system":"round2",
            "source_key":"IMMUTABLE-SOURCE-1", "raw_code":"RAW-CODE-1",
            "raw_name":"原始仓库名", "history_mapping":[],
            "raw_value":{}, "suggestion":{"canonical":"建议仓库名"},
        }, cookie)
        self.assertEqual(status, 201)
        status, _, body = self.request("POST", "/api/v1/review/discover", {
            "entity_type":"warehouse_mapping", "source_system":"round2",
            "source_key":"IMMUTABLE-SOURCE-1", "raw_code":"MUTATED-CODE",
            "raw_name":"原始仓库名", "history_mapping":[],
            "raw_value":{}, "suggestion":{},
        }, cookie)
        self.assertEqual(status, 422)
        self.assertEqual(body["error"], "IMMUTABLE_RAW_FIELDS")
        status, _, body = self.request("POST", "/api/v1/review/confirm", {
            "version_type":"channel_mapping", "version_name":"channel_mapping_v99",
            "item_ids":[item["id"]], "raw_code":"MUTATED", "reason":"非法请求",
        }, cookie)
        self.assertEqual(status, 422)
        self.assertEqual(body["error"], "RAW_FIELDS_READ_ONLY")

    def test_action_list_reads_persisted_ledger(self):
        cookie = self.login()
        status, _, saved = self.request("POST", "/api/v1/actions/upsert", {
            "action_code":"ACT-ROUND2-001", "action_type":"补货",
            "title":"结构化动作记录", "status":"待确认", "sku":"SKU-MOCK",
        }, cookie)
        self.assertEqual(status, 200)
        self.assertEqual(saved["status"], "待确认")
        status, _, body = self.request("GET", "/api/v1/action/list?status=%E5%BE%85%E7%A1%AE%E8%AE%A4", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(body["data"][0]["action_code"], "ACT-ROUND2-001")
        self.assertEqual(body["allowed_statuses"], ["待确认", "已确认", "执行中", "已完成", "已取消"])

    def test_inventory_aging_upload_stays_pending_until_confirmed(self):
        cookie = self.login()
        status, _, saved = self.request("POST", "/api/v1/facts/inventory-aging/upsert", {
            "records":[{"source_record_id":"AGING-MOCK-1","sku_raw":"SKU-MOCK","warehouse_raw_name":"WH-MOCK","age_days":90,"quantity":1,"amount":1,"source_reference":"file://private/mock-aging#1","caliber":"MOCK结构化库龄","confirmation_status":"UNCONFIRMED"}],
            "metadata":{"source_system":"mock-upload","extracted_at":"2026-08-30T00:00:00Z","synced_at":"2026-08-30T00:01:00Z","sync_job_id":"MOCK-AGING-1"},
        }, cookie)
        self.assertEqual(status, 200)
        self.assertEqual(saved["upserted"], 1)
        status, _, body = self.request("GET", "/api/v1/inventory/aging", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual([item["bucket"] for item in body["rows"]], ["<90", "90-180", "180-360", "360+"])
        self.assertEqual(body["confirmation_status"], "待确认")
        self.assertTrue(all(item["amount"] is None for item in body["rows"]))


if __name__ == "__main__":
    unittest.main()
