"""SC Item UOM Conversion — dòng quy đổi đơn vị kép của SC Item.

Mỗi dòng: 1 <uom> = <conversion_factor> đơn vị tồn kho (uom gốc của item).
VD: item base = "Cái"; dòng {uom: Hộp, conversion_factor: 50} nghĩa 1 Hộp = 50 Cái.
"""

from frappe.model.document import Document


class SCItemUOMConversion(Document):
    pass
