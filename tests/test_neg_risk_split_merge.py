import unittest
from unittest.mock import patch, call
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from poly_web3.web3_service.base import BaseWeb3Service
from poly_web3.schema import MergePlanItem
from poly_web3.clob_compat import get_clob_signature_type, get_clob_funder


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

    def build_erc20_approve_tx_data(self, *args, **kwargs) -> str:
        return "0xapprove"

    def build_pusd_wrap_tx_data(self, *args, **kwargs) -> str:
        return "0xwrap"

    def get_redeemable_payout_amount(self, *args, **kwargs) -> int:
        return 0

    def _raise_if_insufficient_split_collateral(self, *args, **kwargs) -> None:
        return None


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
            "0xada200001000ef00d07553cee7006808f895c6f1",
        )
        self.assertEqual(result["txs"][0]["data"], "0xnegsplit")

    def test_merge_routes_to_neg_risk_adapter_when_detected_from_market_api(self):
        with patch.object(
            self.service,
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
            "0xada200001000ef00d07553cee7006808f895c6f1",
        )
        self.assertEqual(result["txs"][0]["data"], "0xnegmerge")

    def test_split_allows_non_negative_risk_market(self):
        with patch.object(
            self.service,
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
            "0xada100874d00e3331d00f2007a9c336a65009718",
        )
        self.assertEqual(result["txs"][0]["data"], "0xsplit")

    def test_split_batch_groups_transactions_by_negative_risk(self):
        result = self.service.split_batch(
            operations=[
                {"condition_id": "0xcond1", "amount": 1, "negative_risk": False},
                {"condition_id": "0xcond2", "amount": 2, "negative_risk": True},
                {"condition_id": "0xcond3", "amount": 3, "negative_risk": True},
            ]
        )

        self.assertEqual(len(result.success_list), 2)
        self.assertEqual(result.error_list, [])
        self.assertEqual(result.success_list[0].negative_risk, False)
        self.assertEqual(result.success_list[0].condition_ids, ["0xcond1"])
        self.assertEqual(result.success_list[0].result["metadata"], "split")
        self.assertEqual(len(result.success_list[0].result["txs"]), 1)
        self.assertEqual(result.success_list[1].negative_risk, True)
        self.assertEqual(result.success_list[1].condition_ids, ["0xcond2", "0xcond3"])
        self.assertEqual(result.success_list[1].result["metadata"], "split")
        self.assertEqual(len(result.success_list[1].result["txs"]), 2)

    def test_merge_batch_supports_per_item_amounts(self):
        with patch.object(
            self.service,
            "build_ctf_merge_tx_data",
            side_effect=["0xmerge1", "0xmerge2"],
        ) as mock_build:
            result = self.service.merge_batch(
                operations=[
                    {"condition_id": "0xcond1", "amount": 1, "negative_risk": False},
                    {"condition_id": "0xcond2", "amount": "2.5", "negative_risk": False},
                ]
            )

        self.assertEqual(len(result.success_list), 1)
        self.assertEqual(result.error_list, [])
        self.assertEqual(result.success_list[0].condition_ids, ["0xcond1", "0xcond2"])
        self.assertEqual(result.success_list[0].result["metadata"], "merge")
        self.assertEqual(
            mock_build.call_args_list,
            [
                call(
                    condition_id="0xcond1",
                    partition=[1, 2],
                    amount=1000000,
                    collateral_token="0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB",
                    parent_collection_id="0x" + "00" * 32,
                ),
                call(
                    condition_id="0xcond2",
                    partition=[1, 2],
                    amount=2500000,
                    collateral_token="0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB",
                    parent_collection_id="0x" + "00" * 32,
                ),
            ],
        )

    def test_split_batch_splits_large_group_by_batch_size(self):
        result = self.service.split_batch(
            operations=[
                {"condition_id": "0xcond1", "amount": 1, "negative_risk": False},
                {"condition_id": "0xcond2", "amount": 2, "negative_risk": False},
                {"condition_id": "0xcond3", "amount": 3, "negative_risk": False},
            ],
            batch_size=2,
        )

        self.assertEqual(len(result.success_list), 2)
        self.assertEqual(result.success_list[0].condition_ids, ["0xcond1", "0xcond2"])
        self.assertEqual(result.success_list[1].condition_ids, ["0xcond3"])
        self.assertEqual(len(result.success_list[0].result["txs"]), 2)
        self.assertEqual(len(result.success_list[1].result["txs"]), 1)

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

    def test_redeem_condition_id_falls_back_to_chain_when_positions_api_is_empty(self):
        self.service.api_client = SimpleNamespace(
            fetch_positions_by_condition_ids=lambda user_address, condition_ids: []
        )
        self.service._resolve_user_address = lambda: "0xuser"
        self.service.is_negative_risk_condition = lambda condition_id: False
        self.service.is_condition_resolved = lambda condition_id: True
        self.service.get_redeemable_index_and_balance = (
            lambda condition_id, collateral_token: [(0, 10)]
        )

        result = self.service.redeem("0xcond1")

        self.assertEqual(result.error_list, [])
        self.assertEqual(len(result.success_list), 1)
        self.assertEqual(result.success_list[0]["metadata"], "redeem")
        self.assertEqual(result.success_list[0]["txs"][0]["data"], "0xredeem")
        self.assertEqual(
            result.success_list[0]["txs"][0]["to"].lower(),
            "0x4d97dcd97ec945f40cf65f87097ace5ea0476045",
        )

    def test_redeem_chain_fallback_can_wrap_redeemed_collateral_to_pusd(self):
        self.service.api_client = SimpleNamespace(
            fetch_positions_by_condition_ids=lambda user_address, condition_ids: []
        )
        self.service._resolve_user_address = lambda: "0xuser"
        self.service.is_negative_risk_condition = lambda condition_id: False
        self.service.is_condition_resolved = lambda condition_id: True
        self.service.get_redeemable_index_and_balance = (
            lambda condition_id, collateral_token: [(0, 10)]
        )
        self.service.get_redeemable_payout_amount = (
            lambda condition_id, collateral_token: 10_000_000
        )

        result = self.service.redeem("0xcond1")

        txs = result.success_list[0]["txs"]
        self.assertEqual([tx["data"] for tx in txs], ["0xredeem", "0xapprove", "0xwrap"])
        self.assertEqual(
            [tx["to"].lower() for tx in txs],
            [
                "0x4d97dcd97ec945f40cf65f87097ace5ea0476045",
                "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
                "0x93070a847efef7f70739046a929d47a521f5b8ee",
            ],
        )

    def test_redeem_condition_id_reports_unresolved_chain_fallback(self):
        self.service.api_client = SimpleNamespace(
            fetch_positions_by_condition_ids=lambda user_address, condition_ids: []
        )
        self.service._resolve_user_address = lambda: "0xuser"
        self.service.is_negative_risk_condition = lambda condition_id: False
        self.service.is_condition_resolved = lambda condition_id: False

        result = self.service.redeem("0xcond1")

        self.assertEqual(result.success_list, [])
        self.assertEqual(result.error_condition_ids, ["0xcond1"])
        self.assertEqual(result.error_list[0].error, "condition is not resolved")

    def test_split_preflight_reports_insufficient_collateral(self):
        service = DummyWeb3Service()
        service._resolve_user_address = lambda: "0xowner"
        service.get_erc20_balance = lambda collateral_token, owner: 5_000_000

        with self.assertRaisesRegex(
            Exception,
            "insufficient exchange collateral balance for split",
        ):
            BaseWeb3Service._raise_if_insufficient_split_collateral(
                service,
                amount_base_units=10_000_000,
                collateral_token="0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB",
            )

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

    def test_merge_all_returns_plan_and_skips_submit_when_no_executable_items(self):
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
            "merge_batch",
            side_effect=AssertionError("merge_batch should not be called"),
        ):
            result = self.service.merge_all(
                min_usdc=50,
                exclude_neg_risk=True,
                max_markets=20,
            )

        self.assertEqual(len(result.plan_list), 1)
        self.assertEqual(result.success_list, [])
        self.assertEqual(result.error_list, [])

    def test_plan_merge_all_uses_mergeable_positions_api(self):
        self.service.api_client = SimpleNamespace(
            fetch_all_mergeable_positions=lambda user_address: [
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
        )
        self.service._resolve_user_address = lambda: "0xuser"

        result = self.service.plan_merge_all(min_usdc=5, exclude_neg_risk=True)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].condition_id, "0xcond1")
        self.assertEqual(result[0].mergeable, 8)
        self.assertIsNone(result[0].reason)

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
            "merge_batch",
            return_value=SimpleNamespace(
                success_list=[
                    SimpleNamespace(
                        negative_risk=False,
                        condition_ids=["0xcond1"],
                        result={"transactionID": "merge-tx"},
                    )
                ],
                error_list=[],
            ),
        ) as mock_merge_batch:
            result = self.service.merge_all(
                min_usdc=5,
                exclude_neg_risk=True,
                max_markets=1,
                batch_size=2,
            )

        self.assertEqual(len(result.plan_list), 2)
        self.assertEqual(len(result.success_list), 1)
        self.assertEqual(result.success_list[0].condition_id, "0xcond1")
        self.assertEqual(result.success_list[0].mergeable, 10)
        self.assertEqual(result.error_list, [])
        mock_merge_batch.assert_called_once_with(
            operations=[
                {
                    "condition_id": "0xcond1",
                    "amount": 10,
                    "negative_risk": False,
                }
            ],
            batch_size=2,
        )

    def test_merge_all_does_not_execute_below_min_usdc(self):
        plan = [
            MergePlanItem(
                condition_id="0xcond1",
                market_slug="market-one",
                yes_balance=4,
                no_balance=4,
                mergeable=4,
                negative_risk=False,
                reason=None,
            )
        ]

        with patch.object(
            DummyWeb3Service,
            "plan_merge_all",
            return_value=plan,
        ), patch.object(
            DummyWeb3Service,
            "merge_batch",
            side_effect=AssertionError("merge_batch should not be called"),
        ):
            result = self.service.merge_all(
                min_usdc=5,
                exclude_neg_risk=True,
                max_markets=20,
            )

        self.assertEqual(result.success_list, [])
        self.assertEqual(result.error_list, [])


class ClobCompatTest(unittest.TestCase):
    def test_reads_signature_type_from_v1_builder_shape(self):
        client = SimpleNamespace(
            builder=SimpleNamespace(sig_type=1, funder="0xfunder")
        )
        self.assertEqual(get_clob_signature_type(client), 1)
        self.assertEqual(get_clob_funder(client), "0xfunder")

    def test_reads_signature_type_from_v2_builder_shape(self):
        client = SimpleNamespace(
            builder=SimpleNamespace(signature_type=2, funder="0xfunder")
        )
        self.assertEqual(get_clob_signature_type(client), 2)
        self.assertEqual(get_clob_funder(client), "0xfunder")


if __name__ == "__main__":
    unittest.main()
