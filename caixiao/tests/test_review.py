from pathlib import Path
import tempfile
import unittest

from caixiao.backend.database import Database
from caixiao.backend.services.review import ReviewService


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp.name) / "review.sqlite3")
        self.review = ReviewService(self.database)
        self.item_id = self.database.upsert_review_item(
            "warehouse_mapping", "jikexyun", "warehouse-1", {"name": "source"}, {"name": "canonical"}, 0.9
        )

    def tearDown(self):
        self.database.close()
        self.temp.cleanup()

    def test_unconfirmed_item_not_in_formal_dimensions(self):
        self.assertEqual(self.review.formal_dimensions("warehouse_mapping"), [])
        self.assertFalse(self.review.is_formal_eligible(["warehouse_mapping"])["eligible"])

    def test_draft_still_not_formal(self):
        version = self.review.confirm("warehouse_mapping", "warehouse_mapping_v1", [self.item_id], "reviewer", reason="首次确认", affected_metrics=["inventory_qty"])
        self.assertEqual(version["status"], "DRAFT")
        self.assertEqual(self.review.formal_dimensions("warehouse_mapping"), [])

    def test_publish_opens_only_matching_gate(self):
        version = self.review.confirm("warehouse_mapping", "warehouse_mapping_v1", [self.item_id], "reviewer", reason="首次确认")
        published = self.review.publish(version["id"], "publisher")
        self.assertEqual(published["status"], "PUBLISHED")
        self.assertEqual(len(self.review.formal_dimensions("warehouse_mapping")), 1)
        gate = self.review.is_formal_eligible(["warehouse_mapping", "sku_mapping"])
        self.assertEqual(gate["missing_published_versions"], ["sku_mapping"])

    def test_invalid_version_name_rejected(self):
        with self.assertRaises(ValueError):
            self.review.confirm("warehouse_mapping", "wrong_v1", [self.item_id], "reviewer", reason="验证")

    def test_mixed_entity_types_rejected(self):
        second = self.database.upsert_review_item("sku_mapping", "jikexyun", "sku-1", {"name": "sku"}, {}, None)
        with self.assertRaises(ValueError):
            self.review.confirm("warehouse_mapping", "warehouse_mapping_v1", [self.item_id, second], "reviewer", reason="验证")

    def test_published_version_is_superseded(self):
        first = self.review.confirm("warehouse_mapping", "warehouse_mapping_v1", [self.item_id], "reviewer", True, "首次发布")
        self.assertEqual(first["status"], "PUBLISHED")
        second = self.review.confirm("warehouse_mapping", "warehouse_mapping_v2", [self.item_id], "reviewer", True, "更新发布")
        versions = {item["version_name"]: item["status"] for item in self.database.list_versions()}
        self.assertEqual(second["status"], "PUBLISHED")
        self.assertEqual(versions["warehouse_mapping_v1"], "SUPERSEDED")

    def test_version_audit_records_full_change_context(self):
        version = self.review.confirm(
            "warehouse_mapping", "warehouse_mapping_v1", [self.item_id], "reviewer",
            True, "仓库归类经人工确认", ["spot_inventory_qty", "operating_inventory_qty"],
        )
        self.assertEqual(version["reason"], "仓库归类经人工确认")
        self.assertEqual(version["affected_metrics"], ["operating_inventory_qty", "spot_inventory_qty"])
        self.assertEqual(version["before"], [])
        self.assertTrue(version["after"])
        self.assertEqual(version["confirmed_by"], "reviewer")
        self.assertIsNotNone(version["confirmed_at"])
        self.assertEqual(version["published_by"], "reviewer")
        self.assertIsNotNone(version["published_at"])

    def test_confirmation_requires_reason(self):
        with self.assertRaises(ValueError):
            self.review.confirm("warehouse_mapping", "warehouse_mapping_v1", [self.item_id], "reviewer")

    def test_raw_name_cannot_be_modified_after_discovery(self):
        with self.assertRaisesRegex(ValueError, "永久只读"):
            self.database.upsert_review_item(
                "warehouse_mapping", "jikexyun", "warehouse-1",
                {"name": "changed"}, {"canonical": "display"}, 0.8,
                raw_code="warehouse-1", raw_name="changed",
            )

    def test_raw_code_cannot_be_modified_after_discovery(self):
        with self.assertRaisesRegex(ValueError, "永久只读"):
            self.database.upsert_review_item(
                "warehouse_mapping", "jikexyun", "warehouse-1",
                {"name": "source"}, {"canonical": "display"}, 0.8,
                raw_code="changed-code", raw_name="source",
            )

    def test_display_name_requires_confirmation_and_publication(self):
        version = self.review.confirm(
            "warehouse_mapping", "warehouse_mapping_v1", [self.item_id], "reviewer",
            False, "确认展示名", ["inventory_qty"],
            [{"item_id": self.item_id, "display_name": "PO确认展示名", "inventory_class": "SPOT"}],
        )
        item = self.database.list_review_items()[0]
        self.assertEqual(item["raw_name"], "source")
        self.assertEqual(item["display_name"], "PO确认展示名")
        self.assertEqual(item["version"], "warehouse_mapping_v1")
        self.assertEqual(self.review.formal_dimensions("warehouse_mapping"), [])
        self.review.publish(version["id"], "publisher")
        published = self.review.formal_dimensions("warehouse_mapping")[0]
        self.assertEqual(published["value"]["display_name"], "PO确认展示名")
        self.assertEqual(published["value"]["canonical"], "PO确认展示名")


if __name__ == "__main__":
    unittest.main()
