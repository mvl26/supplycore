from frappe.model.document import Document
from frappe.utils.nestedset import NestedSet


class SCItemGroup(NestedSet):
    nsm_parent_field = "parent_group"
