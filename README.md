# poly-web3

![PyPI](https://img.shields.io/pypi/v/poly-web3)
![Python](https://img.shields.io/pypi/pyversions/poly-web3)
![License](https://img.shields.io/github/license/tosmart01/poly-web3)

Python SDK for redeeming and splitting/merging Polymarket positions via Proxy/Safe wallets (gas-free).

[English](README.md) | [中文](README.zh.md)

Optional address analysis is available for trading fee impact and PnL curves. See [Address Analysis (Optional)](#address-analysis-optional).

```bash
# required Python >= 3.11
pip install poly-web3
```

```python
from poly_web3 import PolyWeb3Service

service = PolyWeb3Service(
    clob_client=client,
    relayer_client=relayer_client,
)

# Redeem all redeemable positions for the current account.
service.redeem_all(batch_size=10)
service.redeem(condition_ids=["0x..."])

# Split/Merge for binary markets (amount in human pUSD units).
service.split("0x...", 10)
service.merge("0x...", 10)
service.merge_all(min_usdc=1, batch_size=10)

# batch Split/Merge
service.split_batch([{"condition_id": "", "amount": 10}])
service.merge_batch([{"condition_id": "", "amount": 10}])

```

[See the full example](#quick-start)

## Redeem Behavior Notes

- Redeemable positions are fetched via the official Positions API, which typically has ~1 minute latency.
- `redeem` and `redeem_all` return a `RedeemResult` pydantic object with `success_list` and `error_list`.
- `success_list` keeps the raw relayer `execute` result structure; `error_list` exposes `condition_id`, `market_slug`, and `error` for retry/backfill.
- `error_condition_ids` is a shortcut list derived from `error_list`, so you can directly retry with `service.redeem(result.error_condition_ids)`.

## Split/Merge Notes

- `split`/`merge` are designed for binary markets (Yes/No) and use the default partition internally.
- Negative-risk markets are detected via the official Gamma markets API and are routed to the NegRisk Adapter.
- `split`/`merge` route through Polymarket's v2 CTF collateral adapter: pUSD is used as exchange collateral, while the resulting CTF token IDs match the market `clobTokenIds`.

## FAQ

1. **UI shows redeemable, but `redeem_all` returns `[]`**: The official Positions API can be delayed by 1–3 minutes. Wait a bit and retry.
2. **RPC error during redeem**: Switch RPC endpoints by setting `rpc_url` when instantiating `PolyWeb3Service`.
3. **Redeem stuck in `execute`**: The official relayer may be congested. Stop redeeming for 1 hour to avoid nonce looping from repeated submissions.
4. **Relayer client returns 403**: You need to apply for Builder API access and use a valid key. Reference: Polymarket Builders — Introduction: https://docs.polymarket.com/developers/builders/builder-intro
5. **Relayer daily limit**: The official relayer typically limits to 100 requests per day. Prefer batch redeem (`batch_size`) to reduce the number of requests and avoid hitting the limit.

## About the Project

This project is a Python rewrite of Polymarket's official TypeScript implementation of `builder-relayer-client`, designed to provide Python developers with a convenient tool for executing Proxy and Safe wallet redeem operations on Polymarket.

**Important Notes:**
- This project implements official CTF redeem plus binary split/merge operations
- Other features (such as trading, order placement, etc.) are not within the scope of this project

**Some Polymarket-related redeem or write operations implemented in this project depend on access granted through Polymarket's Builder program. To perform real redeem operations against Polymarket, you must apply for and obtain a Builder key/credentials via Polymarket's official Builder application process. After approval you will receive the credentials required to use the Builder API—only then will the redeem flows in this repository work against the live service. For local development or automated tests, use mocks or testnet setups instead of real keys to avoid exposing production credentials.**

Reference：
- Polymarket Builders — Introduction: https://docs.polymarket.com/developers/builders/builder-intro

**Current Status:**
- ✅ **Proxy Wallet** - Fully supported for redeem/split/merge
- ✅ **Safe Wallet** - Fully supported for redeem/split/merge
- 🚧 **EOA Wallet** - Under development

We welcome community contributions! If you'd like to help implement EOA wallet redeem functionality, or have other improvement suggestions, please feel free to submit a Pull Request.

## Installation

```bash
pip install poly-web3
```

Or using uv:

```bash
uv add poly-web3
```

Install with analysis support:

```bash
pip install "poly-web3[analysis]"
```

## Requirements

- Python >= 3.11

## Dependencies

- `py-clob-client-v2 >= 1.0.0` - Polymarket CLOB v2 client
- `py-builder-relayer-client >= 0.0.1` - Builder Relayer client
- `web3 >= 7.0.0` - Web3.py library
- `eth-utils == 5.3.1` - Ethereum utilities library

## Quick Start

### Basic Usage - Redeem

```python
import os
import dotenv
from py_builder_relayer_client.client import RelayClient
from py_builder_signing_sdk.config import BuilderConfig
from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds
from py_clob_client_v2 import ClobClient
from poly_web3 import RELAYER_URL, PolyWeb3Service

dotenv.load_dotenv()

host = "https://clob.polymarket.com"
chain_id = 137
client = ClobClient(
    host,
    key=os.getenv("POLY_API_KEY"),
    chain_id=chain_id,
    signature_type=1,
    funder=os.getenv("POLYMARKET_PROXY_ADDRESS"),
)

client.set_api_creds(client.create_or_derive_api_key())

relayer_client = RelayClient(
    RELAYER_URL,
    chain_id,
    os.getenv("POLY_API_KEY"),
    BuilderConfig(
        local_builder_creds=BuilderApiKeyCreds(
            key=os.getenv("BUILDER_KEY"),
            secret=os.getenv("BUILDER_SECRET"),
            passphrase=os.getenv("BUILDER_PASSPHRASE"),
        )
    ),
)

service = PolyWeb3Service(
    clob_client=client,
    relayer_client=relayer_client,
    rpc_url="https://polygon-bor.publicnode.com",
)

redeem_all_result = service.redeem_all(batch_size=10)
print(redeem_all_result)
if redeem_all_result.error_list:
    print("Redeem all failed items:", redeem_all_result.error_list)
    print("Retry condition ids:", redeem_all_result.error_condition_ids)

condition_ids = [
    "0xaba28be5f981580aa29a123afc8d233dd66c1f236f0d7e1bfffe07777cdb6cc5",
]
redeem_batch_result = service.redeem(condition_ids, batch_size=10)
print(redeem_batch_result)
if redeem_batch_result.error_list:
    print("Redeem batch failed items:", redeem_batch_result.error_list)
    print("Retry condition ids:", redeem_batch_result.error_condition_ids)
```

### Basic Usage - Split/Merge

```python
import os
import dotenv
from py_builder_relayer_client.client import RelayClient
from py_builder_signing_sdk.config import BuilderConfig
from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds
from py_clob_client_v2 import ClobClient
from poly_web3 import RELAYER_URL, PolyWeb3Service

dotenv.load_dotenv()

# Initialize ClobClient
host = "https://clob.polymarket.com"
chain_id = 137  # Polygon mainnet
client = ClobClient(
    host,
    key=os.getenv("POLY_API_KEY"),
    chain_id=chain_id,
    signature_type=1,  # Proxy wallet type (signature_type=2 for Safe)
    funder=os.getenv("POLYMARKET_PROXY_ADDRESS"),
)

client.set_api_creds(client.create_or_derive_api_key())

# Initialize RelayerClient
relayer_client = RelayClient(
    RELAYER_URL,
    chain_id,
    os.getenv("POLY_API_KEY"),
    BuilderConfig(
        local_builder_creds=BuilderApiKeyCreds(
            key=os.getenv("BUILDER_KEY"),
            secret=os.getenv("BUILDER_SECRET"),
            passphrase=os.getenv("BUILDER_PASSPHRASE"),
        )
    ),
)

# Create service instance
service = PolyWeb3Service(
    clob_client=client,
    relayer_client=relayer_client,
    rpc_url="https://polygon-bor.publicnode.com",  # optional
)

condition_id = "0xaba28be5f981580aa29a123afc8d233dd66c1f236f0d7e1bfffe07777cdb6cc5"
amount = 10  # amount in human pUSD units

split_result = service.split(condition_id, amount)
print(split_result)

merge_result = service.merge(condition_id, amount)
print(merge_result)

split_batch_result = service.split_batch([{"condition_id": condition_id, "amount": 10}])
print(split_batch_result.model_dump_json(indent=2))

merge_batch_result = service.merge_batch([{"condition_id": condition_id, "amount": 10}])
print(merge_batch_result.model_dump_json(indent=2))

merge_plan = service.plan_merge_all(min_usdc=5, exclude_neg_risk=True)
for i in merge_plan:
    print(i.model_dump_json(indent=2))

merge_all_result = service.merge_all(min_usdc=1, batch_size=10)
print(merge_all_result)
```

### Address Analysis (Optional)

You can optionally analyze one address for:
- Trading fee impact (`Net PnL` vs `No-Fee PnL`)
- PnL curve and ratio/metrics visualization

![PnL Curve](assets/pnl.png)
![Ratio Metrics](assets/ratio.png)

#### Address Analysis CLI

After installing `poly-web3[analysis]`, you can run:

```bash
analysis-poly-open --address 0xabc --symbols btc,eth --intervals 5,15
```

Or start the base service:

```bash
analysis-poly
```

## API Documentation

### PolyWeb3Service

The main service class that automatically selects the appropriate service implementation based on wallet type.

#### Methods

##### `redeem(condition_ids: str | list[str], batch_size: int = 20, collateral_token: str = CTF_COLLATERAL_TOKEN, wrap_redeemed_collateral: bool = True) -> RedeemResult`

Execute redeem operation. When Polymarket's Positions API does not return positions for explicit `condition_ids`, the service falls back to on-chain CTF balance checks for non-negative-risk markets. By default, redeemed USDC.e is wrapped back into pUSD in the same relayed transaction when the payout can be computed on-chain.

**Parameters:**
- `condition_ids` (str | list[str]): Condition ID or list of condition IDs
- `batch_size` (int): Batch size for redeem requests
- `collateral_token` (str): CTF collateral token used for on-chain fallback, defaults to USDC.e
- `wrap_redeemed_collateral` (bool): Wrap redeemed USDC.e back to pUSD when possible

**Returns:**
- `RedeemResult`: A pydantic object with:
- `success_list`: Raw relayer `execute` result payloads for successful batches
- `error_list`: Failed condition entries with `condition_id`, `market_slug`, and `error`
- `error_condition_ids`: Shortcut list for retry, derived from `error_list`

**Examples:**

```python
# Single condition redeem
result = service.redeem("0x...")

# Batch redeem
result = service.redeem(["0x...", "0x..."], batch_size=10)
```

##### `redeem_all(batch_size: int = 20) -> RedeemResult`

Redeem all positions that are currently redeemable for the authenticated account.

**Returns:**
- `RedeemResult`: Empty `success_list` and `error_list` if no redeemable positions. Partial failures are surfaced in `error_list` instead of returning `None`.

**Examples:**

```python
# Redeem all positions that can be redeemed
service.redeem_all(batch_size=10)
```

See [`examples/example_redeem.py`](examples/example_redeem.py) for a complete redeem example.

##### `split(condition_id: str, amount: int | float | str, negative_risk: bool | None = None)`

Split a binary (Yes/No) position. `amount` is in human pUSD units.

**Parameters:**
- `condition_id` (str): Condition ID
- `amount` (int | float | str): Amount in pUSD
- `negative_risk` (bool | None): Optional explicit market-type hint. When `None`, the SDK auto-detects via the official Gamma markets API and routes neg-risk markets to the NegRisk Adapter.

**Returns:**
- `dict | None`: Transaction result

**Examples:**

```python
result = service.split("0x...", 1.25)
```

##### `merge(condition_id: str, amount: int | float | str, negative_risk: bool | None = None)`

Merge a binary (Yes/No) position. `amount` is in human pUSD units.

**Parameters:**
- `condition_id` (str): Condition ID
- `amount` (int | float | str): Amount in pUSD
- `negative_risk` (bool | None): Optional explicit market-type hint. When `None`, the SDK auto-detects via the official Gamma markets API and routes neg-risk markets to the NegRisk Adapter.

**Returns:**
- `dict | None`: Transaction result

**Examples:**

```python
result = service.merge("0x...", 1.25)
```

##### `plan_merge_all(min_usdc: int | float | str = 5, exclude_neg_risk: bool = True) -> list[MergePlanItem]`

Scan all current positions and compute merge opportunities without submitting transactions.

**Returns:**
- `list[MergePlanItem]`: Each item includes `condition_id`, `market_slug`, `yes_balance`, `no_balance`, `mergeable`, `negative_risk`, and `reason`

**Examples:**

```python
plan = service.plan_merge_all(min_usdc=5, exclude_neg_risk=True)
```

##### `merge_all(min_usdc: int | float | str = 5, exclude_neg_risk: bool = True, max_markets: int = 20, batch_size: int = 10) -> MergeAllResult`

Plan and optionally execute merge operations for current positions.

**Parameters:**
- `min_usdc` (int | float | str): Skip mergeable amounts below this threshold
- `exclude_neg_risk` (bool): Skip neg-risk markets in this first-pass bulk merge flow
- `max_markets` (int): Maximum number of mergeable markets to execute in one call
- `batch_size` (int): Maximum transactions submitted per grouped merge batch

**Returns:**
- `MergeAllResult`: Contains `plan_list`, `success_list`, `error_list`, and `error_condition_ids`

**Examples:**

```python
result = service.merge_all(
    min_usdc=5,
    exclude_neg_risk=True,
    max_markets=20,
    batch_size=10,
)
```


## Project Structure

```
poly_web3/
├── __init__.py              # Main entry point, exports PolyWeb3Service
├── const.py                 # Constant definitions (contract addresses, ABIs, etc.)
├── schema.py                # Data models (WalletType, etc.)
├── signature/               # Signature-related modules
│   ├── build.py            # Proxy wallet derivation and struct hashing
│   ├── hash_message.py     # Message hashing
│   └── secp256k1.py        # secp256k1 signing
└── web3_service/           # Web3 service implementations
    ├── base.py             # Base service class
    ├── proxy_service.py    # Proxy wallet service (✅ Implemented)
    ├── eoa_service.py      # EOA wallet service (🚧 Under development)
    └── safe_service.py     # Safe wallet service (✅ Implemented)
```

## Notes

1. **Environment Variable Security**: Make sure `.env` file is added to `.gitignore`, do not commit sensitive information to the code repository
2. **Network Support**: Currently mainly supports Polygon mainnet (chain_id: 137), Amoy testnet may have limited functionality
3. **Wallet Type**: Proxy (signature_type: 1) and Safe (signature_type: 2) are supported; EOA wallet operations are under development
4. **Gas Fees**: Transactions are executed through Relayer, gas fees are handled by the Relayer

## Development

### Install Development Dependencies

```bash
uv pip install -e ".[dev]"
```

### Run Examples

```bash
python examples/example_redeem.py
python examples/example_split_merge.py
```

### Contributing

Simple contribution flow:

1. Open an Issue to describe the change (bug/feature/doc).
2. Fork and create a branch: `feat/xxx` or `fix/xxx`.
3. Make changes and update/add docs if needed.
4. Run: `uv run python -m examples.example_redeem` or `uv run python -m examples.example_split_merge` (if applicable).
5. Open a Pull Request and link the Issue.

## License

MIT

## Author

PinBar

## Related Links

- [Polymarket](https://polymarket.com/)
- [Polygon Network](https://polygon.technology/)
