# poly-web3

Python SDK for Polymarket Proxy wallet redeem operations. Supports executing Conditional Token Fund (CTF) redeem operations on Polymarket through proxy wallets, Free gas.

[English](README.md) | [中文](README.zh.md)

## About the Project

This project is a Python rewrite of Polymarket's official TypeScript implementation of `builder-relayer-client`, designed to provide Python developers with a convenient tool for executing proxy wallet redeem operations on Polymarket.

**Important Notes:**
- This project **only implements the official redeem functionality**, focusing on Conditional Token Fund (CTF) redeem operations
- Other features (such as trading, order placement, etc.) are not within the scope of this project

**Some Polymarket-related redeem or write operations implemented in this project depend on access granted through Polymarket's Builder program. To perform real redeem operations against Polymarket, you must apply for and obtain a Builder key/credentials via Polymarket's official Builder application process. After approval you will receive the credentials required to use the Builder API—only then will the redeem flows in this repository work against the live service. For local development or automated tests, use mocks or testnet setups instead of real keys to avoid exposing production credentials.**

Reference：
- Polymarket Builders — Introduction: https://docs.polymarket.com/developers/builders/builder-intro

**Current Status:**
- ✅ **Proxy Wallet** - Fully supported for redeem functionality
- 🚧 **Safe Wallet** - Under development
- 🚧 **EOA Wallet** - Under development

We welcome community contributions! If you'd like to help implement Safe or EOA wallet redeem functionality, or have other improvement suggestions, please feel free to submit a Pull Request.

## Features

- ✅ Support for Polymarket Proxy wallet redeem operations (currently only Proxy wallet is supported)
- ✅ Check if conditions are resolved
- ✅ Get redeemable indexes and balances
- ✅ Support for standard CTF redeem and negative risk (neg_risk) redeem
- ✅ Automatic transaction execution through Relayer service

## Installation

```bash
pip install poly-web3
```

Or using uv:

```bash
uv add poly-web3
```

## Requirements

- Python >= 3.11

## Dependencies

- `py-clob-client >= 0.25.0` - Polymarket CLOB client
- `py-builder-relayer-client >= 0.0.1` - Builder Relayer client
- `web3 == 6.8` - Web3.py library
- `eth-utils == 5.3.1` - Ethereum utilities library

## Quick Start

### Basic Usage - Execute Redeem

```python
import os
import dotenv
from py_builder_relayer_client.client import RelayClient
from py_builder_signing_sdk.config import BuilderConfig
from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds
from py_clob_client.client import ClobClient
from poly_web3 import RELAYER_URL, PolyWeb3Service

dotenv.load_dotenv()

# Initialize ClobClient
host = "https://clob.polymarket.com"
chain_id = 137  # Polygon mainnet
client = ClobClient(
    host,
    key=os.getenv("POLY_API_KEY"),
    chain_id=chain_id,
    signature_type=1,  # Proxy wallet type
    funder=os.getenv("POLYMARKET_PROXY_ADDRESS"),
)

client.set_api_creds(client.create_or_derive_api_creds())

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


# Execute redeem operation (batch)
condition_ids = [
    "0xc3df016175463c44f9c9f98bddaa3bf3daaabb14b069fb7869621cffe73ddd1c",
    "0x31fb435a9506d14f00b9de5e5e4491cf2223b6d40a2525d9afa8b620b61b50e2",
]
redeem_batch_result = service.redeem(condition_ids, batch_size=20)
print(f"Redeem batch result: {redeem_batch_result}")

# Redeem all positions that are currently redeemable
redeem_all_result = service.redeem_all(batch_size=20)
print(f"Redeem all result: {redeem_all_result}")
```

### Optional - Query Operations

Before executing redeem, you can optionally check the condition status and query redeemable balances:

```python
# Check if condition is resolved
condition_id = "0xc3df016175463c44f9c9f98bddaa3bf3daaabb14b069fb7869621cffe73ddd1c"
can_redeem = service.is_condition_resolved(condition_id)

# Get redeemable indexes and balances
redeem_balance = service.get_redeemable_index_and_balance(
    condition_id, owner=client.builder.funder
)

print(f"Can redeem: {can_redeem}")
print(f"Redeemable balance: {redeem_balance}")
```

## API Documentation

### PolyWeb3Service

The main service class that automatically selects the appropriate service implementation based on wallet type.

#### Methods

##### `is_condition_resolved(condition_id: str) -> bool`

Check if the specified condition is resolved.

**Parameters:**
- `condition_id` (str): Condition ID (32-byte hexadecimal string)

**Returns:**
- `bool`: Returns `True` if the condition is resolved, otherwise `False`

##### `get_winning_indexes(condition_id: str) -> list[int]`

Get the list of winning indexes.

**Parameters:**
- `condition_id` (str): Condition ID

**Returns:**
- `list[int]`: List of winning indexes

##### `get_redeemable_index_and_balance(condition_id: str, owner: str) -> list[tuple]`

Get redeemable indexes and balances for the specified address.

**Parameters:**
- `condition_id` (str): Condition ID
- `owner` (str): Wallet address

**Returns:**
- `list[tuple]`: List of tuples containing (index, balance), balance is in USDC units

##### `redeem(condition_ids: list[str], batch_size: int = 20)`

Execute redeem operation.

**Parameters:**
- `condition_ids` (list[str]): List of condition IDs
- `batch_size` (int): Batch size for redeem requests

**Returns:**
- `dict | list[dict]`: Transaction result(s) containing transaction status and related information

**Examples:**

```python
# Batch redeem
result = service.redeem(["0x...", "0x..."], batch_size=20)
```

##### `redeem_all(batch_size: int = 20) -> list[dict] | None`

Redeem all positions that are currently redeemable for the authenticated account.

**Returns:**
- `list[dict] | None`: List of redeem results, or `None` if no redeemable positions

**Examples:**

```python
# Redeem all positions that can be redeemed
service.redeem_all(batch_size=20)
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
    └── safe_service.py     # Safe wallet service (🚧 Under development)
```

## Notes

1. **Environment Variable Security**: Make sure `.env` file is added to `.gitignore`, do not commit sensitive information to the code repository
2. **Network Support**: Currently mainly supports Polygon mainnet (chain_id: 137), Amoy testnet may have limited functionality
3. **Wallet Type**: **Currently only Proxy wallet is supported** (signature_type: 1), Safe and EOA wallet redeem functionality is under development
4. **Gas Fees**: Transactions are executed through Relayer, gas fees are handled by the Relayer

## Development

### Install Development Dependencies

```bash
uv pip install -e ".[dev]"
```

### Run Examples

```bash
python examples/example_redeem.py
```

### Contributing

We welcome all forms of contributions! If you'd like to:

- Implement Safe or EOA wallet support
- Fix bugs or improve existing functionality
- Add new features or improve documentation
- Make suggestions or report issues

Please feel free to submit an Issue or Pull Request. Your contributions will help make this project better!

## License

MIT

## Author

PinBar

## Related Links

- [Polymarket](https://polymarket.com/)
- [Polygon Network](https://polygon.technology/)
