import unittest

from caixiao.backend.sandbox import SANDBOX_LABEL, compare_inventory, compare_sales


class SandboxDiffTests(unittest.TestCase):
    def test_sales_difference_has_requested_breakdowns(self):
        old = [
            {"trade_no": "A", "amount": 100, "channel_raw_name": "CH1", "store_raw_name": "S1", "sku_raw": "K1"},
            {"trade_no": "B", "amount": 50, "channel_raw_name": "CH1", "store_raw_name": "S2", "sku_raw": "K2"},
        ]
        new = [
            {"trade_no": "A", "payment": 90, "pay_time": "2026-08-01", "channel_raw_name": "CH1", "store_raw_name": "S1", "sku_raw": "K1"},
            {"trade_no": "C", "payment": 40, "pay_time": "2026-08-01", "channel_raw_name": "CH2", "store_raw_name": "S3", "sku_raw": "K3"},
        ]
        result = compare_sales(old, new)
        self.assertEqual(result["label"], SANDBOX_LABEL)
        self.assertEqual(result["old_sales_amount"], 150)
        self.assertEqual(result["new_sales_amount_by_pay_time"], 130)
        self.assertEqual(result["only_old_orders"], ["B"])
        self.assertEqual(result["only_new_orders"], ["C"])
        self.assertEqual(result["amount_mismatch_orders"][0]["trade_no"], "A")
        self.assertTrue(result["channel_differences"])
        self.assertFalse(result["formal_kpi_enabled"])

    def test_inventory_difference_has_mapping_delta(self):
        old = [{"warehouse_raw_name": "WH1", "sku_raw": "K1", "quantity": 10, "amount": 100}]
        new = [{"warehouse_raw_name": "WH2", "sku_raw": "K1", "quantity": 7, "amount": 80}]
        result = compare_inventory(old, new)
        self.assertEqual(result["quantity"]["difference"], -3)
        self.assertEqual(result["amount"]["difference"], -20)
        self.assertEqual(len(result["mapping_differences"]["only_old"]), 1)
        self.assertEqual(len(result["mapping_differences"]["only_new"]), 1)

    def test_inventory_detects_changed_mapping(self):
        old = [{"warehouse_raw_name":"WH1","sku_raw":"K1","quantity":1,"amount":1,"warehouse_mapped":"OLD","inventory_class":"SPOT"}]
        new = [{"warehouse_raw_name":"WH1","sku_raw":"K1","quantity":1,"amount":1,"warehouse_mapped":"NEW","inventory_class":"IN_TRANSIT"}]
        result = compare_inventory(old, new)
        self.assertEqual(len(result["mapping_differences"]["changed"]), 1)


if __name__ == "__main__":
    unittest.main()
