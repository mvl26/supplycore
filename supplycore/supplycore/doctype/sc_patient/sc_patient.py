"""SC Patient — bệnh nhân với validate số thẻ BHYT format VN."""

import re
import frappe
from frappe import _
from frappe.model.document import Document


# QAv3-BUG-M0-09: Format số thẻ BHYT theo Quyết định 1351/QĐ-BHXH/2015:
# 2 chữ Mã đối tượng (DN/HC/CC/HX/HT/TB/CB/NO/CT/XK/TY/HN/DT/DK/XB/TC/...)
# + 1 số Mức hưởng (1-5)
# + 2 số Mã tỉnh (01-99)
# + 10 số Mã thẻ (số tự nhiên)
# Total 15 ký tự, có thể có dấu '-' sau mỗi nhóm.
# Pattern accept:
#   HC4-101-1234567890   (cách bằng '-')
#   HC41011234567890     (liền)
BHYT_CARD_REGEX = re.compile(r"^[A-Z]{2}[1-5]-?[0-9]{2}-?[0-9]{10}$")


class SCPatient(Document):
    def validate(self):
        self._validate_bhyt_card_no()

    def _validate_bhyt_card_no(self):
        if not self.bhyt_card_no:
            return  # BHYT optional
        clean = self.bhyt_card_no.strip().upper().replace(" ", "")
        if not BHYT_CARD_REGEX.match(clean):
            frappe.throw(_(
                "SC-E022 INVALID_BHYT_CARD: Số thẻ BHYT '{0}' không đúng định "
                "dạng VN. Phải gồm 2 chữ mã đối tượng + 1 số mức hưởng + 2 số "
                "mã tỉnh + 10 số mã thẻ (vd: HC4-101-1234567890). "
                "Tham chiếu QĐ 1351/QĐ-BHXH/2015."
            ).format(self.bhyt_card_no), title="SC-E022 INVALID_BHYT_CARD")
        # Normalize: bỏ dấu '-' khi lưu
        self.bhyt_card_no = clean.replace("-", "")
