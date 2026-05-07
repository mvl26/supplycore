from frappe.utils.nestedset import NestedSet


class SCGLAccount(NestedSet):
    nsm_parent_field = "parent_account"
