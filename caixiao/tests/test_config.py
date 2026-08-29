from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from caixiao.backend.config import Settings


class ConfigTests(unittest.TestCase):
    def valid_settings(self, **changes):
        values = dict(
            host="127.0.0.1", port=8010, db_path=Path(tempfile.gettempdir()) / "config-test.sqlite3",
            allowed_origins=("http://127.0.0.1:8010",), token_secret="s" * 32,
            bootstrap_user="", bootstrap_password="", session_ttl_seconds=60,
            sandbox_snapshot_dir="", jky={},
        )
        values.update(changes)
        return Settings(**values)

    def test_valid_server_settings(self):
        self.valid_settings().validate_for_server()

    def test_short_secret_rejected(self):
        with self.assertRaises(ValueError):
            self.valid_settings(token_secret="short").validate_for_server()

    def test_wildcard_cors_rejected(self):
        with self.assertRaises(ValueError):
            self.valid_settings(allowed_origins=("*",)).validate_for_server()

    def test_incomplete_bootstrap_rejected(self):
        with self.assertRaises(ValueError):
            self.valid_settings(bootstrap_user="admin").validate_for_server()

    def test_weak_bootstrap_password_rejected(self):
        with self.assertRaises(ValueError):
            self.valid_settings(bootstrap_user="admin", bootstrap_password="weak").validate_for_server()

    def test_from_env_reads_explicit_values(self):
        with patch.dict("os.environ", {
            "CAIXIAO_HOST":"0.0.0.0", "CAIXIAO_PORT":"9000", "CAIXIAO_DB_PATH":"/tmp/test.sqlite3",
            "CAIXIAO_ALLOWED_ORIGINS":"https://one.example,https://two.example",
            "CAIXIAO_TOKEN_SECRET":"s" * 32, "JKY_BASE_URL":"https://api.example.invalid",
        }, clear=True):
            settings = Settings.from_env()
        self.assertEqual(settings.host, "0.0.0.0")
        self.assertEqual(settings.port, 9000)
        self.assertEqual(settings.db_path, Path("/tmp/test.sqlite3"))
        self.assertEqual(len(settings.allowed_origins), 2)
        self.assertEqual(settings.jky["base_url"], "https://api.example.invalid")


if __name__ == "__main__":
    unittest.main()
