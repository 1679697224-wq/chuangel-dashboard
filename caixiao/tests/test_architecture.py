from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "caixiao" / "backend"


class FormalPipelineIsolationTests(unittest.TestCase):
    def test_formal_backend_does_not_import_legacy_dsh_pipeline(self):
        violations = []
        for path in BACKEND_ROOT.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "dsh_keys" in text:
                violations.append(path.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(violations, [])

    def test_formal_sales_sync_has_no_business_time_filter(self):
        from caixiao.backend.etl import plan_sales_sync

        for supports_modified in (True, False):
            plan = plan_sales_sync(None, supports_modified=supports_modified)
            self.assertIsNone(plan["business_time_filter"])
            self.assertNotEqual(plan["cursor_field"], "consign_time")
            self.assertEqual(plan["upsert_key"], ["source_system", "trade_no", "line_id"])


if __name__ == "__main__":
    unittest.main()
