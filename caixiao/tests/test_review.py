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
        version = self.review.confirm("warehouse_mapping", "warehouse_mapping_v1", [self.item_id], "reviewer")
        self.assertEqual(version["status"], "DRAFT")
        self.assertEqual(self.review.formal_dimensions("warehouse_mapping"), [])

    def test_publish_opens_only_matching_gate(self):
        version = self.review.confirm("warehouse_mapping", "warehouse_mapping_v1", [self.item_id], "reviewer")
        published = self.review.publish(version["id"], "publisher")
        self.assertEqual(published["status"], "PUBLISHED")
        self.assertEqual(len(self.review.formal_dimensions("warehouse_mapping")), 1)
        gate = self.review.is_formal_eligible(["warehouse_mapping", "sku_mapping"])
        self.assertEqual(gate["missing_published_versions"], ["sku_mapping"])

    def test_invalid_version_name_rejected(self):
        with self.assertRaises(ValueError):
            self.review.confirm("warehouse_mapping", "wrong_v1", [self.item_id], "reviewer")

    def test_mixed_entity_types_rejected(self):
        second = self.database.upsert_review_item("sku_mapping", "jikexyun", "sku-1", {"name": "sku"}, {}, None)
        with self.assertRaises(ValueError):
            self.review.confirm("warehouse_mapping", "warehouse_mapping_v1", [self.item_id, second], "reviewer")

    def test_published_version_is_superseded(self):
        first = self.review.confirm("warehouse_mapping", "warehouse_mapping_v1", [self.item_id], "reviewer", True)
        self.assertEqual(first["status"], "PUBLISHED")
        second = self.review.confirm("warehouse_mapping", "warehouse_mapping_v2", [self.item_id], "reviewer", True)
        versions = {item["version_name"]: item["status"] for item in self.database.list_versions()}
        self.assertEqual(second["status"], "PUBLISHED")
        self.assertEqual(versions["warehouse_mapping_v1"], "SUPERSEDED")


if __name__ == "__main__":
    unittest.main()
