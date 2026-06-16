"""Hợp đồng JSON canonical giữa tool và hệ thống import. Có version."""
import jsonschema
from .errors import ExtractError

SCHEMA_VERSION = 1

_LINE = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "tt": {"type": "integer"},
        "name": {"type": "string"}, "his_code": {"type": "string"},
        "uom": {"type": "string"}, "batch_no": {"type": "string"},
        "expiry": {"type": "string"}, "qty": {"type": "number"},
        "unit_price": {"type": "number"}, "amount": {"type": "number"},
    },
    "required": ["tt", "name", "his_code", "uom", "batch_no", "expiry",
                 "qty", "unit_price", "amount"],
}

CANONICAL_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "slip_type": {"type": "string"},
        "profile": {"type": "string"},
        "slip_no": {"type": "string"}, "slip_date": {"type": "string"},
        "from_warehouse_name": {"type": "string"},
        "to_warehouse_name": {"type": "string"},
        "lines": {"type": "array", "items": _LINE},
    },
    "required": ["schema_version", "slip_type", "profile", "slip_no",
                 "slip_date", "from_warehouse_name", "to_warehouse_name", "lines"],
}


def validate(data: dict) -> dict:
    try:
        jsonschema.validate(data, CANONICAL_SCHEMA)
    except jsonschema.ValidationError as e:
        raise ExtractError(f"JSON canonical không hợp lệ: {e.message}") from e
    return data
