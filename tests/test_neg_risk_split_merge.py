import unittest
from unittest.mock import patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from poly_web3.web3_service.base import BaseWeb3Service


class DummyWeb3Service(BaseWeb3Service):
    def __init__(self):
        pass

    submit_results = None

    def _build_redeem_tx(self, to: str, data: str):
        return {"to": to, "data": data}

    def _submit_transactions(self, txs, metadata: str):
        if self.submit_results:
            result = self.submit_results.pop(0)
            if isinstance(result, Exception):
                raise result
            return result
        return {"txs": txs, "metadata": metadata}

    def build_ctf_split_tx_data(self, *args, **kwargs) -> str:
        return "0xsplit"

    def build_ctf_merge_tx_data(self, *args, **kwargs) -> str:
        return "0xmerge"

    def build_ctf_redeem_tx_data(self, *args, **kwargs) -> str:
        return "0xredeem"

    def build_neg_risk_split_tx_data(self, *args, **kwargs) -> str:
        return "0xnegsplit"

    def build_neg_risk_merge_tx_data(self, *args, **kwargs) -> str:
        return "0xnegmerge"

    def build_neg_risk_redeem_tx_data(self, *args, **kwargs) -> str:
        return "0xnegredeem"


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

    def test_redeem_from_positions_returns_structured_success_and_error_lists(self):
        self.service.submit_results = [
            {"transactionID": "tx-success"},
            Exception("rpc timeout"),
        ]
        positions = [
            {
                "conditionId": "0xcond1",
                "slug": "market-one",
                "negativeRisk": False,
                "avgPrice": 0.5,
                "size": 2,
            },
            {
                "conditionId": "0xcond2",
                "slug": "market-two",
                "negativeRisk": False,
                "avgPrice": 0.5,
                "size": 2,
            },
        ]

        result = self.service._redeem_from_positions(positions, batch_size=1)

        self.assertEqual(result.success_list, [{"transactionID": "tx-success"}])
        self.assertEqual(len(result.error_list), 1)
        self.assertEqual(result.error_condition_ids, ["0xcond2"])
        self.assertEqual(result.error_list[0].condition_id, "0xcond2")
        self.assertEqual(result.error_list[0].market_slug, "market-two")
        self.assertEqual(result.error_list[0].error, "rpc timeout")

    def test_redeem_from_positions_treats_none_submit_result_as_error(self):
        self.service.submit_results = [None]
        positions = [
            {
                "conditionId": "0xcond1",
                "slug": "market-one",
                "negativeRisk": False,
                "avgPrice": 0.5,
                "size": 2,
            }
        ]

        result = self.service._redeem_from_positions(positions, batch_size=1)

        self.assertEqual(result.success_list, [])
        self.assertEqual(len(result.error_list), 1)
        self.assertEqual(result.error_condition_ids, ["0xcond1"])
        self.assertEqual(result.error_list[0].condition_id, "0xcond1")
        self.assertEqual(result.error_list[0].market_slug, "market-one")
        self.assertIn("returned None", result.error_list[0].error)


if __name__ == "__main__":
    unittest.main()
