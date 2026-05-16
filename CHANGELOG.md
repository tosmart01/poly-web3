# Changelog

## 2.0.2

- Extend `DepositWalletWeb3Service.DEFAULT_DEADLINE_SEC` from 240 seconds to 14,400 seconds to avoid `deadline too soon` failures when submitting deposit-wallet batches.

## 2.0.1

- Add `POLY_1271` deposit wallet support and route redeem/split/merge batches through `execute_deposit_wallet_batch`.
- Raise the minimum `py-builder-relayer-client` dependency to `0.0.2rc1` because earlier releases do not provide the deposit-wallet batch APIs used by this release.

## 2.0.0

- Migrate CLOB dependency and client compatibility to `py-clob-client-v2`.
- Add Polymarket v2 pUSD collateral routing for split/merge through the CTF collateral adapters.
- Route negative-risk split/merge through the v2 negative-risk CTF collateral adapter.
- Add redeem post-processing to wrap redeemed USDC.e back into pUSD for continued Polymarket v2 trading.
- Update examples, README files, and regression tests for the v2 split/redeem workflow.

## 1.0.7

- Refactor HTTP requests into a dedicated API client with URL constants and shared `requests.Session` usage.
- Add batch `split_batch` and `merge_batch` APIs with per-market amounts, `negative_risk` grouping, and configurable `batch_size`.
- Update `merge_all` to use batch merge execution, honor `min_usdc` explicitly, and document the new workflow in examples and README files.

## 1.0.6

- Add NegRisk Adapter split/merge support for binary negative-risk markets.
- Auto-detect `negRisk` markets through the Gamma markets API and route split/merge accordingly.
- Add regression tests for neg-risk split/merge routing.

## 1.0.1

- Fix web3 7.x compatibility for calldata encoding and checksum helpers.
- Keep redeem flow compatible across web3 6/7 in proxy and base services.
