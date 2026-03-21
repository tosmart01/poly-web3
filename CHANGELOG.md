# Changelog

## 1.0.6

- Add NegRisk Adapter split/merge support for binary negative-risk markets.
- Auto-detect `negRisk` markets through the Gamma markets API and route split/merge accordingly.
- Add regression tests for neg-risk split/merge routing.

## 1.0.1

- Fix web3 7.x compatibility for calldata encoding and checksum helpers.
- Keep redeem flow compatible across web3 6/7 in proxy and base services.
