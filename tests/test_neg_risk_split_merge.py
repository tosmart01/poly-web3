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

    def test_build_merge_plan_from_positions_marks_missing_side_and_neg_risk(self):
        positions = [
            {
                "conditionId": "0xcond1",
                "slug": "market-one",
                "outcomeIndex": 0,
                "size": 120,
                "negativeRisk": False,
            },
            {
                "conditionId": "0xcond1",
                "slug": "market-one",
                "outcomeIndex": 1,
                "size": 80,
                "negativeRisk": False,
            },
            {
                "conditionId": "0xcond2",
                "slug": "market-two",
                "outcomeIndex": 0,
                "size": 50,
                "negativeRisk": False,
            },
            {
                "conditionId": "0xcond3",
                "slug": "market-three",
                "outcomeIndex": 0,
                "size": 40,
                "negativeRisk": True,
            },
            {
                "conditionId": "0xcond3",
                "slug": "market-three",
                "outcomeIndex": 1,
                "size": 40,
                "negativeRisk": True,
            },
        ]

        result = self.service._build_merge_plan_from_positions(
            positions=positions,
            min_usdc=5,
            exclude_neg_risk=True,
        )

        self.assertEqual(len(result), 3)
        by_condition = {item.condition_id: item for item in result}

        self.assertEqual(by_condition["0xcond1"].mergeable, 80)
        self.assertIsNone(by_condition["0xcond1"].reason)

        self.assertEqual(by_condition["0xcond2"].mergeable, 0)
        self.assertEqual(by_condition["0xcond2"].reason, "missing_opposite_side")

        self.assertEqual(by_condition["0xcond3"].mergeable, 40)
        self.assertEqual(by_condition["0xcond3"].reason, "negative_risk_excluded")

    def test_merge_all_dry_run_returns_plan_without_executing(self):
        positions = [
            {
                "conditionId": "0xcond1",
                "slug": "market-one",
                "outcomeIndex": 0,
                "size": 10,
                "negativeRisk": False,
            },
            {
                "conditionId": "0xcond1",
                "slug": "market-one",
                "outcomeIndex": 1,
                "size": 8,
                "negativeRisk": False,
            },
        ]

        plan = self.service._build_merge_plan_from_positions(
            positions=positions,
            min_usdc=5,
            exclude_neg_risk=True,
        )

        with patch.object(
            DummyWeb3Service,
            "plan_merge_all",
            return_value=plan,
        ), patch.object(
            DummyWeb3Service,
            "merge",
            side_effect=AssertionError("merge should not be called"),
        ):
            result = self.service.merge_all(
                min_usdc=5,
                exclude_neg_risk=True,
                dry_run=True,
                max_markets=20,
            )

        self.assertTrue(result.dry_run)
        self.assertEqual(len(result.plan_list), 1)
        self.assertEqual(result.success_list, [])
        self.assertEqual(result.error_list, [])

    def test_merge_all_executes_up_to_max_markets(self):
        positions = [
            {
                "conditionId": "0xcond1",
                "slug": "market-one",
                "outcomeIndex": 0,
                "size": 12,
                "negativeRisk": False,
            },
            {
                "conditionId": "0xcond1",
                "slug": "market-one",
                "outcomeIndex": 1,
                "size": 10,
                "negativeRisk": False,
            },
            {
                "conditionId": "0xcond2",
                "slug": "market-two",
                "outcomeIndex": 0,
                "size": 9,
                "negativeRisk": False,
            },
            {
                "conditionId": "0xcond2",
                "slug": "market-two",
                "outcomeIndex": 1,
                "size": 9,
                "negativeRisk": False,
            },
        ]

        plan = self.service._build_merge_plan_from_positions(
            positions=positions,
            min_usdc=5,
            exclude_neg_risk=True,
        )

        with patch.object(
            DummyWeb3Service,
            "plan_merge_all",
            return_value=plan,
        ), patch.object(
            DummyWeb3Service,
            "merge",
            return_value={"transactionID": "merge-tx"},
        ) as mock_merge:
            result = self.service.merge_all(
                min_usdc=5,
                exclude_neg_risk=True,
                dry_run=False,
                max_markets=1,
            )

        self.assertFalse(result.dry_run)
        self.assertEqual(len(result.plan_list), 2)
        self.assertEqual(len(result.success_list), 1)
        self.assertEqual(result.success_list[0].condition_id, "0xcond1")
        self.assertEqual(result.success_list[0].mergeable, 10)
        self.assertEqual(result.error_list, [])
        self.assertEqual(mock_merge.call_count, 1)


if __name__ == "__main__":
    unittest.main()
