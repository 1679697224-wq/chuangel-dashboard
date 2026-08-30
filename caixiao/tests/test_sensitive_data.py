from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]


class SensitiveDataCleanupTests(unittest.TestCase):
    def test_master_fill_sources_have_no_embedded_business_totals(self):
        pattern = re.compile(
            r'["\'](?:amount|qty|normal|demo|defect)["\']\s*:\s*-?\d{3,}(?:\.\d+)?'
        )
        for name in ("master_fill.py", "master_fill2.py", "master_fill3.py"):
            source = (REPO_ROOT / "dsh_keys" / name).read_text(encoding="utf-8")
            self.assertEqual(pattern.findall(source), [], name)
            self.assertIn("load_runtime_business_data()", source)

    def test_runtime_business_data_requires_explicit_mode(self):
        source = (REPO_ROOT / "dsh_keys/runtime_business_data.py").read_text(encoding="utf-8")
        self.assertIn("RUNTIME_PRIVATE", source)
        self.assertIn("MOCK", source)
        self.assertIn("CHUANGEL_ALLOW_MOCK_BUSINESS_DATA", source)

    def test_traffic_token_is_not_in_worktree_and_is_ignored(self):
        self.assertFalse((REPO_ROOT / "客流爬虫/data/token.txt").exists())
        ignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("客流爬虫/data/token*", ignore)
        client = (REPO_ROOT / "客流爬虫/lib/ipva.js").read_text(encoding="utf-8")
        self.assertIn("IPVA_ACCESS_TOKEN", client)
        self.assertIn("IPVA_TOKEN_FILE", client)


if __name__ == "__main__":
    unittest.main()
