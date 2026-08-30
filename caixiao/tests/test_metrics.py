from pathlib import Path
import tempfile
import unittest

from caixiao.backend.database import Database
from caixiao.backend.services.metrics import MetricsService, calculate_dual_woi
from caixiao.backend.services.review import ReviewService


class MetricsGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp.name) / "metrics.sqlite3")
        self.review = ReviewService(self.database)
        self.metrics = MetricsService(self.review, self.database)
        self.version_counts = {}

    def tearDown(self):
        self.database.close()
        self.temp.cleanup()

    def publish(self, version_type, source_key, suggestion):
        item_id = self.database.upsert_review_item(version_type, "test", source_key, {"raw": source_key}, suggestion, 1.0)
        count = self.version_counts.get(version_type, 0) + 1
        self.version_counts[version_type] = count
        return self.review.confirm(version_type, "{}_v{}".format(version_type, count), [item_id], "po", True, "测试发布", ["test_metric"])

    def publish_many(self, version_type, entries):
        item_ids = [
            self.database.upsert_review_item(version_type, "test", source_key, {"raw": source_key}, suggestion, 1.0)
            for source_key, suggestion in entries
        ]
        count = self.version_counts.get(version_type, 0) + 1
        self.version_counts[version_type] = count
        return self.review.confirm(version_type, "{}_v{}".format(version_type, count), item_ids, "po", True, "测试批量发布", ["test_metric"])

    @staticmethod
    def sales_fact(trade_no="T1", line_id="L1", status="已完成", payment=100, quantity=1, warehouse="WH1", channel="CH1", sku="SKU1", pay="2026-07-31T23:00:00", consign="2026-08-03T12:00:00"):
        return {
            "source_system": "jikexyun", "source_record_id": trade_no + line_id,
            "trade_no": trade_no, "line_id": line_id, "create_time": "2026-07-31T22:00:00",
            "pay_time": pay, "audit_time": "2026-08-01T00:00:00", "consign_time": consign,
            "complete_time": "2026-08-05T00:00:00", "modified_time": "2026-08-05T01:00:00",
            "trade_status": status, "quantity": quantity, "payment": payment,
            "warehouse_raw_name": warehouse, "channel_raw_name": channel, "store_raw_name": "STORE1",
            "goods_no": "G1", "sku_raw": sku, "source_api": "orders.modified",
            "raw_json_reference": "blob://sales/" + trade_no + "/" + line_id,
            "extracted_at": "2026-08-05T01:01:00Z", "synced_at": "2026-08-05T01:02:00Z", "sync_job_id": "JOB1",
        }

    @staticmethod
    def inventory_fact(record_id, warehouse, quantity, amount=0, sku="SKU1"):
        return {
            "source_system": "jikexyun", "source_record_id": record_id,
            "snapshot_time": "2026-08-05T02:00:00Z", "warehouse_raw_name": warehouse,
            "sku_raw": sku, "quantity": quantity, "amount": amount, "source_api": "inventory.snapshot",
            "raw_json_reference": "blob://inventory/" + record_id, "extracted_at": "2026-08-05T02:01:00Z",
            "synced_at": "2026-08-05T02:02:00Z", "sync_job_id": "JOB2",
        }

    def publish_sales_chain(self, statuses=None):
        self.publish("warehouse_mapping", "WH1", {"canonical": "WH-C", "inventory_class": "SPOT"})
        self.publish("channel_mapping", "CH1", {"canonical": "CH-C"})
        self.publish("sku_mapping", "SKU1", {"canonical": "SKU-C"})
        self.publish("sales_caliber", "default", {"time_field": "pay_time", "woi_window_days": 28})
        self.publish_many("sales_adjustment_rules", list((statuses or {"已完成": {"action": "INCLUDE"}}).items()))

    def test_unconfirmed_facts_cannot_bypass_gate(self):
        self.database.upsert_sales_facts([self.sales_fact()])
        result = self.metrics.sales_summary()
        self.assertFalse(result["gate"]["eligible"])
        self.assertIn("sales_caliber", result["gate"]["missing_published_versions"])
        self.assertTrue(all(item["value"] is None for item in result["data"]))

    def test_unavailable_global_filter_is_not_silently_ignored(self):
        self.publish_sales_chain()
        self.database.upsert_sales_facts([self.sales_fact()])
        result = self.metrics.sales_summary(filters={"brand":"Apple"})
        self.assertFalse(result["gate"]["eligible"])
        self.assertEqual(result["gate"]["pending_filter_fields"], ["brand"])
        self.assertTrue(all(item["value"] is None for item in result["data"]))

    def test_confirmed_but_unpublished_version_is_blocked(self):
        item_id = self.database.upsert_review_item("sales_caliber", "test", "default", {}, {"time_field": "pay_time"}, 1.0)
        self.review.confirm("sales_caliber", "sales_caliber_v1", [item_id], "po", False, "仅确认未发布")
        self.database.upsert_sales_facts([self.sales_fact()])
        result = self.metrics.sales_summary()
        self.assertIn("sales_caliber", result["gate"]["missing_published_versions"])

    def test_pay_time_cross_month_enters_sales_after_full_gate(self):
        self.publish_sales_chain()
        self.database.upsert_sales_facts([self.sales_fact()])
        result = self.metrics.sales_summary()
        self.assertTrue(result["gate"]["eligible"])
        self.assertEqual(result["sales_time_field"], "pay_time")
        self.assertEqual(result["data"][0]["value"], 100)

    def test_status_exclude_and_refund_offset_are_configured(self):
        self.publish_sales_chain({"已完成": {"action": "INCLUDE"}, "取消": {"action": "EXCLUDE"}, "退款": {"action": "OFFSET", "multiplier": -1}})
        self.database.upsert_sales_facts([
            self.sales_fact("T1", "L1", "已完成", 100),
            self.sales_fact("T2", "L1", "取消", 80),
            self.sales_fact("T3", "L1", "退款", 20),
        ])
        result = self.metrics.sales_summary()
        self.assertEqual(result["data"][0]["value"], 80)
        self.assertEqual(result["data"][1]["value"], 2)

    def test_pending_adjustment_blocks_formal_sales(self):
        self.publish_sales_chain({"退货": {"action": "PENDING"}})
        self.database.upsert_sales_facts([self.sales_fact(status="退货")])
        result = self.metrics.sales_summary()
        self.assertFalse(result["gate"]["eligible"])
        self.assertTrue(any("PENDING" in item for item in result["gate"]["unmapped_facts"]))

    def test_unknown_adjustment_action_is_blocked(self):
        self.publish_sales_chain({"已完成": {"action": "AUTO_GUESS"}})
        self.database.upsert_sales_facts([self.sales_fact()])
        result = self.metrics.sales_summary()
        self.assertFalse(result["gate"]["eligible"])
        self.assertTrue(any("动作无效" in item for item in result["gate"]["unmapped_facts"]))

    def test_three_inventory_calibers_exclude_non_operating(self):
        self.publish_many("warehouse_mapping", [
            (warehouse, {"canonical": warehouse + "-C", "inventory_class": classification})
            for warehouse, classification in (("WH1", "SPOT"), ("WH2", "IN_TRANSIT"), ("WH3", "EXCLUDE"))
        ])
        self.publish("sku_mapping", "SKU1", {"canonical": "SKU-C"})
        self.publish("inventory_caliber", "default", {"operating_formula": "SPOT+IN_TRANSIT", "operating_classes": ["SPOT", "IN_TRANSIT"]})
        self.database.upsert_inventory_facts([
            self.inventory_fact("I1", "WH1", 10, 100), self.inventory_fact("I2", "WH2", 5, 50),
            self.inventory_fact("I3", "WH3", 99, 990),
        ])
        result = self.metrics.inventory_summary()
        values = {item["code"]: item["value"] for item in result["data"]}
        self.assertEqual(values["spot_inventory_qty"], 10)
        self.assertEqual(values["in_transit_inventory_qty"], 5)
        self.assertEqual(values["operating_inventory_qty"], 15)
        self.assertEqual(values["inventory_value"], 150)

    def test_unconfirmed_warehouse_blocks_inventory(self):
        self.publish("warehouse_mapping", "WH1", {"canonical": "WH-C", "inventory_class": "SPOT"})
        self.publish("sku_mapping", "SKU1", {"canonical": "SKU-C"})
        self.publish("inventory_caliber", "default", {"operating_formula": "SPOT+IN_TRANSIT", "operating_classes": ["SPOT", "IN_TRANSIT"]})
        self.database.upsert_inventory_facts([self.inventory_fact("I1", "UNKNOWN", 10)])
        result = self.metrics.inventory_summary()
        self.assertFalse(result["gate"]["eligible"])
        self.assertTrue(any("UNKNOWN" in item for item in result["gate"]["unmapped_facts"]))

    def test_dual_woi_zero_cases_and_configured_window(self):
        self.assertEqual(calculate_dual_woi(0, 0, 0)["state"], "NO_INVENTORY_NO_SALES")
        self.assertEqual(calculate_dual_woi(1, 0, 0)["state"], "INVENTORY_WITHOUT_SALES")
        self.assertEqual(calculate_dual_woi(0, 0, 1)["state"], "SALES_WITHOUT_INVENTORY")
        calculated = calculate_dual_woi(14, 14, 28, 28)
        self.assertEqual(calculated["spot"], 2)
        self.assertEqual(calculated["operating"], 4)

    def test_dual_woi_flows_through_published_versions(self):
        self.publish_sales_chain()
        self.publish("inventory_caliber", "default", {"operating_classes": ["SPOT", "IN_TRANSIT"]})
        self.database.upsert_sales_facts([self.sales_fact(quantity=28)])
        self.database.upsert_inventory_facts([self.inventory_fact("I1", "WH1", 14, 140)])
        result = self.metrics.woi_summary()
        values = {item["code"]: item["value"] for item in result["data"]}
        self.assertTrue(result["gate"]["eligible"])
        self.assertEqual(values["spot_woi"], 2)
        self.assertEqual(values["operating_woi"], 2)

    def test_sales_daily_uses_published_caliber_and_filters(self):
        self.publish_sales_chain()
        self.database.upsert_sales_facts([
            self.sales_fact("T1", "L1", pay="2026-08-01T09:00:00", payment=100),
            self.sales_fact("T2", "L1", pay="2026-08-02T09:00:00", payment=50),
        ])
        result = self.metrics.sales_daily({"start": "2026-08-02", "end": "2026-08-02", "channel": "CH-C"})
        self.assertTrue(result["gate"]["eligible"])
        self.assertEqual(result["sales_time_field"], "pay_time")
        self.assertEqual(result["rows"], [{
            "date": "2026-08-02", "sales_amount": 50.0, "order_count": 1,
            "source": "吉客云销售事实层", "caliber": "pay_time",
            "updated_at": "2026-08-05T01:02:00Z", "status": "正式",
        }])

    def test_inventory_aging_reads_confirmed_structured_records(self):
        self.publish("warehouse_mapping", "WH1", {"canonical": "WH-C", "inventory_class": "SPOT"})
        self.publish("sku_mapping", "SKU1", {"canonical": "SKU-C"})
        self.publish("inventory_caliber", "default", {"operating_classes": ["SPOT", "IN_TRANSIT"]})
        self.database.upsert_inventory_aging_records([
            {"source_system":"upload","source_record_id":"A1","sku_raw":"SKU1","warehouse_raw_name":"WH1","age_days":30,"quantity":2,"amount":20,"source_reference":"file://private/aging#A1","caliber":"结构化上传库龄天数","extracted_at":"2026-08-30T00:00:00Z","synced_at":"2026-08-30T00:01:00Z","sync_job_id":"AGING1","confirmation_status":"CONFIRMED"},
            {"source_system":"upload","source_record_id":"A2","sku_raw":"SKU1","warehouse_raw_name":"WH1","age_days":360,"quantity":1,"amount":10,"source_reference":"file://private/aging#A2","caliber":"结构化上传库龄天数","extracted_at":"2026-08-30T00:00:00Z","synced_at":"2026-08-30T00:01:00Z","sync_job_id":"AGING1","confirmation_status":"CONFIRMED"},
        ])
        result = self.metrics.inventory_aging()
        values = {item["bucket"]: item for item in result["rows"]}
        self.assertEqual(values["<90"]["quantity"], 2)
        self.assertEqual(values["360+"]["amount"], 10)
        self.assertEqual(result["confirmation_status"], "已确认")

    def test_anomaly_list_requires_published_thresholds_then_calculates(self):
        pending = self.metrics.anomaly_list()
        self.assertEqual(len(pending["data"]), 5)
        self.assertTrue(all(item["conclusion"] is None for item in pending["data"]))
        self.publish_sales_chain()
        self.publish("inventory_caliber", "default", {"operating_classes": ["SPOT", "IN_TRANSIT"]})
        self.publish("anomaly_thresholds", "default", {"stockout_qty_max": 0, "high_inventory_qty_min": 10, "long_aging_amount_min": 5, "slow_moving_woi_min": 1})
        self.database.upsert_sales_facts([self.sales_fact(quantity=28)])
        self.database.upsert_inventory_facts([self.inventory_fact("I1", "WH1", 14, 140)])
        self.database.upsert_inventory_aging_records([
            {"source_system":"upload","source_record_id":"A1","sku_raw":"SKU1","warehouse_raw_name":"WH1","age_days":360,"quantity":1,"amount":10,"source_reference":"file://private/aging#A1","caliber":"结构化上传库龄天数","extracted_at":"2026-08-30T00:00:00Z","synced_at":"2026-08-30T00:01:00Z","sync_job_id":"AGING1","confirmation_status":"CONFIRMED"}
        ])
        result = self.metrics.anomaly_list()
        indexed = {item["type"]: item for item in result["data"]}
        self.assertEqual(indexed["高库存"]["status"], "异常")
        self.assertEqual(indexed["长库龄"]["status"], "异常")
        self.assertEqual(indexed["政策风险"]["status"], "待接入")


if __name__ == "__main__":
    unittest.main()
