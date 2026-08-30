from datetime import datetime, timezone
import unittest

from caixiao.backend.etl import build_status_review, canonical_sales_fact, plan_sales_sync


class SalesEtlTests(unittest.TestCase):
    def test_modified_time_is_incremental_cursor(self):
        plan = plan_sales_sync("2026-08-01T00:00:00+00:00", datetime(2026, 8, 2, tzinfo=timezone.utc), True)
        self.assertEqual(plan["strategy"], "MODIFIED_INCREMENTAL")
        self.assertEqual(plan["cursor_field"], "modified_time")
        self.assertIsNone(plan["business_time_filter"])

    def test_fallback_uses_lookback_and_upsert(self):
        plan = plan_sales_sync(None, datetime(2026, 8, 10, tzinfo=timezone.utc), False, 9)
        self.assertEqual(plan["strategy"], "ROLLING_LOOKBACK_UPSERT")
        self.assertEqual(plan["lookback_days"], 9)
        self.assertEqual(plan["upsert_key"], ["source_system", "trade_no", "line_id"])

    def test_pay_time_order_crossing_consign_month_is_preserved(self):
        raw = {
            "trade_no": "T1", "line_id": "L1", "create_time": "2026-07-31T22:00:00",
            "pay_time": "2026-07-31T23:00:00", "audit_time": "2026-08-01T00:01:00",
            "consign_time": "2026-08-03T12:00:00", "complete_time": "2026-08-05T12:00:00",
            "modified_time": "2026-08-05T13:00:00", "trade_status": "已完成",
            "quantity": 1, "payment": 100, "warehouse_raw_name": "WH-A",
            "channel_raw_name": "CH-A", "store_raw_name": "STORE-A", "goods_no": "G1",
            "sku_raw": "SKU-1", "source_api": "orders.modified", "raw_json_reference": "blob://sales/T1/L1",
        }
        metadata = {"source_system": "jikexyun", "source_record_id": "R1", "extracted_at": "2026-08-05T13:01:00Z", "synced_at": "2026-08-05T13:02:00Z", "sync_job_id": "JOB-1"}
        fact = canonical_sales_fact(raw, {}, metadata)
        self.assertEqual(fact["pay_time"][:7], "2026-07")
        self.assertEqual(fact["consign_time"][:7], "2026-08")
        self.assertEqual(fact["modified_time"], "2026-08-05T13:00:00")

    def test_status_review_never_auto_confirms(self):
        review = build_status_review([
            {"trade_no": "T1", "trade_status": "已完成", "payment": 100},
            {"trade_no": "T2", "trade_status": "退款", "payment": -20},
        ])
        self.assertTrue(all(item["human_confirmation_status"] == "待PO确认" for item in review))
        self.assertTrue(all(item["count_as_sales"] is None for item in review))

    def test_raw_json_cannot_be_written_as_reference(self):
        raw = {
            "trade_no":"T1","line_id":"L1","trade_status":"已完成","quantity":1,"payment":1,
            "warehouse_raw_name":"WH","channel_raw_name":"CH","goods_no":"G","sku_raw":"K",
            "source_api":"orders.modified","raw_json_reference":"{\"sensitive\":true}",
        }
        metadata = {"source_system":"jikexyun","source_record_id":"R1","extracted_at":"x","synced_at":"y","sync_job_id":"j"}
        with self.assertRaises(ValueError):
            canonical_sales_fact(raw, {}, metadata)


if __name__ == "__main__":
    unittest.main()
