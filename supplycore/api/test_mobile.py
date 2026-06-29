import frappe
import unittest
from supplycore.api.mobile import mobile_login


class TestMobileLogin(unittest.TestCase):
    def setUp(self):
        self.email = "mobiletest@example.com"
        if not frappe.db.exists("User", self.email):
            frappe.get_doc({
                "doctype": "User",
                "email": self.email,
                "first_name": "Mobile",
                "send_welcome_email": 0,
                "new_password": "Secret#12345",
            }).insert(ignore_permissions=True)
        frappe.db.commit()

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_valid_login_returns_token(self):
        res = mobile_login(self.email, "Secret#12345")
        self.assertEqual(res["user"], self.email)
        self.assertTrue(res["api_key"])
        self.assertTrue(res["api_secret"])
        self.assertIn("roles", res)

    def test_invalid_password_raises(self):
        with self.assertRaises(frappe.AuthenticationError):
            mobile_login(self.email, "wrong-password")

    def test_disabled_user_raises(self):
        frappe.db.set_value("User", self.email, "enabled", 0)
        frappe.db.commit()
        try:
            with self.assertRaises(frappe.AuthenticationError):
                mobile_login(self.email, "Secret#12345")
        finally:
            frappe.db.set_value("User", self.email, "enabled", 1)
            frappe.db.commit()
