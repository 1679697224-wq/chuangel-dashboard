import time
import unittest

from caixiao.backend.auth import hash_password, issue_token, verify_password, verify_token


class AuthTests(unittest.TestCase):
    def test_password_round_trip(self):
        encoded = hash_password("a-strong-test-password")
        self.assertTrue(verify_password("a-strong-test-password", encoded))
        self.assertFalse(verify_password("wrong-password", encoded))
        self.assertTrue(encoded.startswith("pbkdf2_sha256$"))

    def test_token_round_trip_and_tamper(self):
        secret = "s" * 40
        token, payload = issue_token("reviewer", secret, 60)
        self.assertEqual(verify_token(token, secret)["sub"], "reviewer")
        self.assertEqual(verify_token(token, "x" * 40), None)
        self.assertEqual(verify_token(token + "bad", secret), None)
        self.assertGreater(payload["exp"], int(time.time()))

    def test_expired_token_is_rejected(self):
        token, _ = issue_token("reviewer", "s" * 40, -1)
        self.assertIsNone(verify_token(token, "s" * 40))


if __name__ == "__main__":
    unittest.main()
