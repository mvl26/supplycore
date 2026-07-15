"""SC Customer -- master khách hàng M7 Sales (BRU-CUS-002)."""

import frappe
from frappe import _
from frappe.model.document import Document

# Role chức năng cổng + role nhãn (xem api/portal.py, setup/ensure_customer_role.py).
PORTAL_ROLE = "SC Customer Portal"
CUSTOMER_ROLE = "Khách hàng"


class SCCustomer(Document):

    def validate(self):
        # Tự tạo tài khoản Portal khi nhân viên Miyano tạo khách hàng mới có email.
        # Chạy TRƯỚC các check để portal_user được set kịp cho BRU-CUS-001 (cho
        # phép tạo khách "Hoạt động" ngay mà không cần bấm nút provision riêng).
        self._auto_provision_portal()
        self._validate_portal_user_unique()
        self._validate_portal_required_for_active()

    def after_insert(self):
        # Gửi email đặt mật khẩu (best-effort) sau khi khách đã lưu — tách khỏi
        # validate để không gửi nhầm khi lưu thất bại. SMTP chưa cấu hình -> chỉ log.
        invite_user = self.flags.get("_portal_invite_user")
        if invite_user:
            try:
                frappe.get_doc("User", invite_user).reset_password(send_email=True)
            except Exception:
                frappe.log_error(frappe.get_traceback(),
                                 f"SC Customer auto-provision: gửi email đặt mật khẩu thất bại ({invite_user})")

    def _auto_provision_portal(self):
        """Nhân viên Miyano tạo khách: nhập `email` (+ tuỳ chọn `portal_password`)
        -> tạo/lấy Website User + gán role (SC Customer Portal + Khách hàng) + set
        portal_user + đặt mật khẩu nhân viên cấp. Idempotent. KHÔNG lưu mật khẩu
        trên hồ sơ khách (xoá sau khi dùng)."""
        password = (self.get("portal_password") or "").strip()

        # Khách đã có tài khoản: cho phép nhân viên đổi/đặt lại mật khẩu nếu nhập.
        if self.portal_user:
            if password:
                self._set_user_password(self.portal_user, password)
            self.portal_password = None
            return

        email = (self.get("email") or "").strip().lower()
        if not email:
            self.portal_password = None
            return
        frappe.utils.validate_email_address(email, throw=True)
        if password and len(password) < 6:
            frappe.throw(_("Mật khẩu Portal tối thiểu 6 ký tự."))

        new_user = not frappe.db.exists("User", email)
        if new_user:
            user = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": self.customer_name or email,
                "user_type": "Website User",
                "send_welcome_email": 0,
            })
            user.flags.ignore_permissions = True
            user.insert(ignore_permissions=True)
        else:
            user = frappe.get_doc("User", email)

        user.add_roles(PORTAL_ROLE)
        if frappe.db.exists("Role", CUSTOMER_ROLE):
            user.add_roles(CUSTOMER_ROLE)  # nhãn 'Khách hàng' (kèm role chức năng)

        # BRU-CUS-002: user chưa gắn khách khác (check unique bên dưới cũng chặn,
        # nhưng báo sớm rõ ràng hơn khi email đã thuộc khách khác).
        other = frappe.db.get_value(
            "SC Customer", {"portal_user": user.name, "name": ["!=", self.name or ""]}, "name")
        if other:
            frappe.throw(_(
                "BRU-CUS-002: Email {0} đã là Tài khoản Portal của khách hàng {1}."
            ).format(user.name, other))

        self.portal_user = user.name
        if password:
            # Nhân viên tự đặt mật khẩu -> cấp trực tiếp cho khách, không cần email reset.
            self._set_user_password(user.name, password)
        elif new_user:
            # Không đặt mật khẩu -> gửi email đặt mật khẩu (best-effort) ở after_insert.
            self.flags._portal_invite_user = user.name

        # KHÔNG lưu mật khẩu plaintext trên hồ sơ khách.
        self.portal_password = None

    @staticmethod
    def _set_user_password(user, password):
        from frappe.utils.password import update_password
        update_password(user, password)

    def _validate_portal_user_unique(self):
        if not self.portal_user:
            return
        if frappe.db.exists("SC Customer", {
            "portal_user": self.portal_user,
            "name": ["!=", self.name or ""],
        }):
            frappe.throw(_(
                "BRU-CUS-002: Tài khoản Portal {0} đã được gán cho khách hàng khác"
            ).format(self.portal_user))

    def _validate_portal_required_for_active(self):
        if self.status == "Hoạt động" and not self.portal_user:
            frappe.throw(_(
                "BRU-CUS-001: Khách hàng phải có tài khoản Portal trước khi kích hoạt (Hoạt động)."
            ))
