"""Patch: seed master data đặc thù bệnh viện Việt Nam (idempotent)."""

from supplycore.setup.seed_master_data import run


def execute():
    run()
