# Changelog

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
