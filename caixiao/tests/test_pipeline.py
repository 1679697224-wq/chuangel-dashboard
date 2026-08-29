import unittest

from caixiao.backend.pipeline import (
    SALES_TIME_FIELDS,
    build_sales_trace,
    clean_sales_record,
    inventory_relationship_check,
    recompute_five_time_views,
    sales_amount_by_time,
)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "created": "2026-08-01 10:00:00",
            "paid": "2026-08-02 10:00:00",
            "audit_time": "2026-08-03 10:00:00",
            "consign_time": "2026-08-04 10:00:00",
            "complete_time": "2026-08-05 10:00:00",
            "amount": "100.50",
            "channel": "raw-channel",
        }
        self.mapping = {"create_time": "created", "pay_time": "paid", "amount": "amount", "channel": "channel"}

    def test_clean_preserves_five_times(self):
        cleaned = clean_sales_record(self.record, self.mapping)
        for field in SALES_TIME_FIELDS:
            self.assertIn(field, cleaned)
        self.assertEqual(cleaned["pay_time"], self.record["paid"])

    def test_trace_blocks_unpublished_mapping(self):
        trace = build_sales_trace(self.record, "src-1", "2026-08-29T00:00:00Z", self.mapping, {}, None)
        self.assertFalse(trace["eligible_for_formal_kpi"])
        self.assertEqual(trace["mapping_state"], "UNCONFIRMED")
        self.assertEqual(trace["source_record_id"], "src-1")

    def test_trace_maps_dimension_with_version(self):
        trace = build_sales_trace(
            self.record,
            "src-1",
            "2026-08-29T00:00:00Z",
            self.mapping,
            {"channel": {"raw-channel": "canonical-channel"}},
            "channel_mapping_v1",
        )
        self.assertTrue(trace["eligible_for_formal_kpi"])
        self.assertEqual(trace["mapped"]["channel"], "canonical-channel")

    def test_recompute_all_five_time_views(self):
        views = recompute_five_time_views([clean_sales_record(self.record, self.mapping)], "amount")
        self.assertEqual(set(views), set(SALES_TIME_FIELDS))
        self.assertEqual(views["pay_time"]["2026-08-02"], 100.5)

    def test_invalid_time_field_is_rejected(self):
        with self.assertRaises(ValueError):
            sales_amount_by_time([], "unknown_time", "amount")

    def test_inventory_relationship(self):
        self.assertTrue(inventory_relationship_check(10, 3, 7)["valid"])
        result = inventory_relationship_check(10, 2, 7)
        self.assertFalse(result["valid"])
        self.assertEqual(result["difference"], 1.0)

    def test_inventory_non_numeric(self):
        self.assertEqual(inventory_relationship_check("bad", 1, 1)["reason"], "NON_NUMERIC")


if __name__ == "__main__":
    unittest.main()
