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
        # Xoá bộ đếm lockout để mỗi test bắt đầu sạch
        frappe.cache.hdel("login_failed_count", self.email)
        frappe.cache.hdel("login_failed_time", self.email)

    def tearDown(self):
        frappe.set_user("Administrator")
        # Dọn cache sau test
        frappe.cache.hdel("login_failed_count", self.email)
        frappe.cache.hdel("login_failed_time", self.email)

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

    def test_brute_force_lockout(self):
        """Sau khi vượt ngưỡng đăng nhập sai, tài khoản phải bị khoá."""
        # Cấu hình System Settings: khoá sau 2 lần sai (ngưỡng thấp để test nhanh)
        sys_settings = frappe.get_doc("System Settings")
        original_max = sys_settings.allow_consecutive_login_attempts
        original_interval = sys_settings.allow_login_after_fail
        sys_settings.allow_consecutive_login_attempts = 2
        sys_settings.allow_login_after_fail = 300  # 5 phút
        sys_settings.save(ignore_permissions=True)
        frappe.db.commit()

        try:
            # Đăng nhập sai 3 lần (> ngưỡng 2) để trip lockout
            for i in range(3):
                try:
                    mobile_login(self.email, "wrong-password")
                except (frappe.AuthenticationError, frappe.SecurityException):
                    pass  # Bỏ qua lỗi authentication bình thường

            # Lần thứ 4 phải bị SecurityException do lockout
            with self.assertRaises(frappe.SecurityException):
                mobile_login(self.email, "wrong-password")

        finally:
            # Khôi phục System Settings gốc
            sys_settings.reload()
            sys_settings.allow_consecutive_login_attempts = original_max
            sys_settings.allow_login_after_fail = original_interval
            sys_settings.save(ignore_permissions=True)
            frappe.db.commit()
