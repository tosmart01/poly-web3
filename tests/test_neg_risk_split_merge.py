import unittest
from unittest.mock import patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from poly_web3.web3_service.base import BaseWeb3Service


class DummyWeb3Service(BaseWeb3Service):
    def __init__(self):
        pass

    def _build_redeem_tx(self, to: str, data: str):
        return {"to": to, "data": data}

    def _submit_transactions(self, txs, metadata: str):
        return {"txs": txs, "metadata": metadata}

    def build_ctf_split_tx_data(self, *args, **kwargs) -> str:
        return "0xsplit"

    def build_ctf_merge_tx_data(self, *args, **kwargs) -> str:
        return "0xmerge"

    def build_neg_risk_split_tx_data(self, *args, **kwargs) -> str:
        return "0xnegsplit"

    def build_neg_risk_merge_tx_data(self, *args, **kwargs) -> str:
        return "0xnegmerge"


class NegRiskSplitMergeGuardTest(unittest.TestCase):
    def setUp(self):
        self.service = DummyWeb3Service()

    def test_split_routes_to_neg_risk_adapter_when_explicitly_marked(self):
        result = self.service.split(
            condition_id="0xabc",
            amount=1,
            negative_risk=True,
        )
        self.assertEqual(result["metadata"], "split")
        self.assertEqual(
            result["txs"][0]["to"].lower(),
            "0xd91e80cf2e7be2e162c6513ced06f1dd0da35296",
        )
        self.assertEqual(result["txs"][0]["data"], "0xnegsplit")

    def test_merge_routes_to_neg_risk_adapter_when_detected_from_market_api(self):
        with patch.object(
            BaseWeb3Service,
            "get_market_by_condition_id",
            return_value={"negRisk": True},
        ):
            result = self.service.merge(
                condition_id="0xdef",
                amount=1,
            )
        self.assertEqual(result["metadata"], "merge")
        self.assertEqual(
            result["txs"][0]["to"].lower(),
            "0xd91e80cf2e7be2e162c6513ced06f1dd0da35296",
        )
        self.assertEqual(result["txs"][0]["data"], "0xnegmerge")

    def test_split_allows_non_negative_risk_market(self):
        with patch.object(
            BaseWeb3Service,
            "get_market_by_condition_id",
            return_value={"negRisk": False},
        ):
            result = self.service.split(
                condition_id="0x123",
                amount=1,
            )
        self.assertEqual(result["metadata"], "split")
        self.assertEqual(
            result["txs"][0]["to"].lower(),
            "0x4d97dcd97ec945f40cf65f87097ace5ea0476045",
        )
        self.assertEqual(result["txs"][0]["data"], "0xsplit")


if __name__ == "__main__":
    unittest.main()
