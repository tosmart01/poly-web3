# -*- coding = utf-8 -*-
# @Time: 2025/12/19 15:31
# @Author: PinBar
# @Site:
# @File: model.py
# @Software: PyCharm
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class WalletType(str, Enum):
    EOA = "EOA"
    SAFE = "SAFE"
    PROXY = "PROXY"

    @classmethod
    def get_with_code(cls, code: int):
        if code == 0:
            return cls.EOA
        elif code == 1:
            return cls.PROXY
        elif code == 2:
            return cls.SAFE


class RedeemErrorItem(BaseModel):
    condition_id: str
    market_slug: str | None = None
    error: str


class RedeemResult(BaseModel):
    success_list: list[dict[str, Any]] = Field(default_factory=list)
    error_list: list[RedeemErrorItem] = Field(default_factory=list)

    @computed_field
    @property
    def error_condition_ids(self) -> list[str]:
        condition_ids: list[str] = []
        seen: set[str] = set()
        for item in self.error_list:
            if item.condition_id in seen:
                continue
            seen.add(item.condition_id)
            condition_ids.append(item.condition_id)
        return condition_ids


class MergePlanItem(BaseModel):
    condition_id: str
    market_slug: str | None = None
    yes_balance: float
    no_balance: float
    mergeable: float
    negative_risk: bool
    reason: str | None = None


class MergeSuccessItem(BaseModel):
    condition_id: str
    market_slug: str | None = None
    mergeable: float
    result: dict[str, Any]


class MergeErrorItem(BaseModel):
    condition_id: str
    market_slug: str | None = None
    mergeable: float
    error: str


class MergeAllResult(BaseModel):
    dry_run: bool = False
    plan_list: list[MergePlanItem] = Field(default_factory=list)
    success_list: list[MergeSuccessItem] = Field(default_factory=list)
    error_list: list[MergeErrorItem] = Field(default_factory=list)

    @computed_field
    @property
    def error_condition_ids(self) -> list[str]:
        condition_ids: list[str] = []
        seen: set[str] = set()
        for item in self.error_list:
            if item.condition_id in seen:
                continue
            seen.add(item.condition_id)
            condition_ids.append(item.condition_id)
        return condition_ids
