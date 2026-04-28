# -*- coding = utf-8 -*-
from typing import Any


def get_clob_signature_type(clob_client: Any) -> int:
    builder = getattr(clob_client, "builder", None)
    for obj, attr in (
        (builder, "sig_type"),
        (builder, "signature_type"),
        (clob_client, "signature_type"),
    ):
        value = getattr(obj, attr, None) if obj is not None else None
        if value is not None:
            return int(value)
    return 0


def get_clob_funder(clob_client: Any) -> str | None:
    builder = getattr(clob_client, "builder", None)
    return getattr(builder, "funder", None) or getattr(clob_client, "funder", None)
