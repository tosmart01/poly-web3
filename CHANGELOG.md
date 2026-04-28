# Changelog

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
