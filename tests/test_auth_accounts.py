from __future__ import annotations

import unittest

from seedance_web import server


class AccountProfileTests(unittest.TestCase):
    def test_editor_account_preserves_display_name_in_public_response(self) -> None:
        user = server.make_auth_user("editor_01", "password-123", "customer", "剪辑小王")

        public_user = server.public_auth_user(user)

        self.assertEqual(user["displayName"], "剪辑小王")
        self.assertEqual(public_user["displayName"], "剪辑小王")
        self.assertEqual(public_user["role"], "customer")

    def test_legacy_user_uses_username_as_display_name(self) -> None:
        user = server.make_auth_user("editor_02", "password-123", "customer")
        user.pop("displayName")

        normalized = server.normalize_auth_user(user)

        self.assertIsNotNone(normalized)
        self.assertEqual(normalized["displayName"], "editor_02")


if __name__ == "__main__":
    unittest.main()
