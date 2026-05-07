from frappe import _


def get_data():
    return [
        {
            "module_name": "Supplycore",
            "category":    "Modules",
            "label":       _("SupplyCore"),
            "color":       "#1E88E5",
            "icon":        "octicon octicon-package",
            "type":        "module",
            "description": "Quản lý chuỗi cung ứng vật tư y tế",
        },
    ]
