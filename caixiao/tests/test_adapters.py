import json
from pathlib import Path
import tempfile
import unittest

from caixiao.backend.adapters.jikexyun import JikexyunAdapter
from caixiao.backend.adapters.snapshot import SnapshotAdapter


class AdapterTests(unittest.TestCase):
    def test_jikexyun_is_disabled_without_config(self):
        adapter = JikexyunAdapter({})
        cards = adapter.review_cards()
        self.assertEqual(len(cards), 4)
        self.assertTrue(all(not card["configured"] for card in cards))
        with self.assertRaises(RuntimeError):
            adapter.fetch("sales", {})

    def test_unknown_domain_is_rejected(self):
        with self.assertRaises(ValueError):
            JikexyunAdapter({}).fetch("unknown", {})

    def test_snapshot_only_reads_allowlisted_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "sales_agg.json").write_text(json.dumps([{"field": 1}]), encoding="utf-8")
            (path / "not_allowed.json").write_text(json.dumps({"secret": 1}), encoding="utf-8")
            result = SnapshotAdapter(directory).inspect()
            self.assertEqual(result["label"], "快照验证")
            self.assertEqual([item["name"] for item in result["files"]], ["sales_agg.json"])
            self.assertFalse(result["formal_kpi_enabled"])
            self.assertFalse(result["files"][0]["data_values_exposed"])

    def test_missing_snapshot_directory(self):
        result = SnapshotAdapter("").inspect()
        self.assertEqual(result["status"], "待接入")


if __name__ == "__main__":
    unittest.main()
