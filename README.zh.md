# poly-web3

Polymarket Proxy 钱包赎回操作的 Python SDK。支持通过代理钱包（Proxy Wallet）在 Polymarket 上执行条件代币基金（CTF）的赎回操作。

[English](README.md) | 中文

## 关于项目

本项目是对Polymarket 官方 TypeScript 实现的 `builder-relayer-client` 的 Python 重写版本，旨在为 Python 开发者提供在 Polymarket 上执行代理钱包赎回操作的便捷工具。

**重要说明：**
- 本项目**仅实现了官方的 redeem（赎回）功能**，专注于条件代币基金（CTF）的赎回操作
- 其他功能（如交易、下单等）不在本项目的实现范围内

**当前状态：**
- ✅ **Proxy 代理钱包** - 已完全支持 redeem 功能
- 🚧 **Safe 钱包** - 开发中
- 🚧 **EOA 钱包** - 开发中

我们欢迎社区贡献！如果您想帮助实现 Safe 或 EOA 钱包的 redeem 功能支持，或者有其他改进建议，欢迎提交 Pull Request。

## 功能特性

- ✅ 支持 Polymarket Proxy 代理钱包赎回操作（当前仅支持 Proxy 钱包）
- ✅ 检查条件是否已解决（resolved）
- ✅ 获取可赎回的索引和余额
- ✅ 支持标准 CTF 赎回和负风险（neg_risk）赎回
- ✅ 自动通过 Relayer 服务执行交易


## 安装

```bash
pip install poly-web3
```

或者使用 uv：

```bash
uv add poly-web3
```

## 环境要求

- Python >= 3.11

## 依赖项

- `py-clob-client >= 0.25.0` - Polymarket CLOB 客户端
- `py-builder-relayer-client >= 0.0.1` - Builder Relayer 客户端
- `web3 == 6.8` - Web3.py 库
- `eth-utils == 5.3.1` - Ethereum 工具库

## 快速开始

### 基本使用 - 执行赎回

```python
import os
import dotenv
from py_builder_relayer_client.client import RelayClient
from py_builder_signing_sdk.config import BuilderConfig
from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds
from py_clob_client.client import ClobClient
from poly_web3 import RELAYER_URL, PolyWeb3Service

dotenv.load_dotenv()

# 初始化 ClobClient
host = "https://clob.polymarket.com"
chain_id = 137  # Polygon 主网
client = ClobClient(
    host,
    key=os.getenv("POLY_API_KEY"),
    chain_id=chain_id,
    signature_type=1,  # Proxy 钱包类型
    funder=os.getenv("POLYMARKET_PROXY_ADDRESS"),
)

client.set_api_creds(client.create_or_derive_api_creds())

# 初始化 RelayerClient
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

# 创建服务实例
service = PolyWeb3Service(clob_client=client, relayer_client=relayer_client)

# 执行赎回操作
condition_id = "0xc3df016175463c44f9c9f98bddaa3bf3daaabb14b069fb7869621cffe73ddd1c"
redeem_result = service.redeem(condition_id=condition_id)
print(f"赎回结果: {redeem_result}")
```

### 可选 - 查询操作

在执行赎回之前，您可以选择性地检查条件状态和查询可赎回余额：

```python
# 检查条件是否已解决
condition_id = "0xc3df016175463c44f9c9f98bddaa3bf3daaabb14b069fb7869621cffe73ddd1c"
can_redeem = service.is_condition_resolved(condition_id)

# 获取可赎回的索引和余额
redeem_balance = service.get_redeemable_index_and_balance(
    condition_id, owner=client.builder.funder
)

print(f"可赎回: {can_redeem}")
print(f"可赎回余额: {redeem_balance}")
```

## API 文档

### PolyWeb3Service

主要的服务类，根据钱包类型自动选择合适的服务实现。

#### 方法

##### `is_condition_resolved(condition_id: str) -> bool`

检查指定的条件是否已解决。

**参数:**
- `condition_id` (str): 条件 ID（32 字节的十六进制字符串）

**返回:**
- `bool`: 如果条件已解决返回 `True`，否则返回 `False`

##### `get_winning_indexes(condition_id: str) -> list[int]`

获取获胜的索引列表。

**参数:**
- `condition_id` (str): 条件 ID

**返回:**
- `list[int]`: 获胜索引的列表

##### `get_redeemable_index_and_balance(condition_id: str, owner: str) -> list[tuple]`

获取指定地址可赎回的索引和余额。

**参数:**
- `condition_id` (str): 条件 ID
- `owner` (str): 钱包地址

**返回:**
- `list[tuple]`: 包含 (index, balance) 元组的列表，余额单位为 USDC

##### `redeem(condition_id: str, neg_risk: bool = False, redeem_amounts: list[int] | None = None)`

执行赎回操作。

**参数:**
- `condition_id` (str): 条件 ID
- `neg_risk` (bool): 是否为负风险赎回，默认为 `False`
- `redeem_amounts` (list[int] | None): 负风险赎回时的金额列表，必须包含 2 个元素

**返回:**
- `dict`: 交易结果，包含交易状态和相关信息

**示例:**

```python
# 标准 CTF 赎回
result = service.redeem(condition_id="0x...")

# 负风险赎回
result = service.redeem(
    condition_id="0x...",
    neg_risk=True,
    redeem_amounts=[1000000, 2000000]  # 单位为最小单位（6 位小数）
)
```

## 项目结构

```
poly_web3/
├── __init__.py              # 主入口，导出 PolyWeb3Service
├── const.py                 # 常量定义（合约地址、ABI 等）
├── schema.py                # 数据模型（WalletType 等）
├── signature/               # 签名相关模块
│   ├── build.py            # 代理钱包派生和结构哈希
│   ├── hash_message.py     # 消息哈希
│   └── secp256k1.py        # secp256k1 签名
└── web3_service/           # Web3 服务实现
    ├── base.py             # 基础服务类
    ├── proxy_service.py    # Proxy 钱包服务（✅ 已实现）
    ├── eoa_service.py      # EOA 钱包服务（🚧 开发中）
    └── safe_service.py     # Safe 钱包服务（🚧 开发中）
```

## 注意事项

1. **环境变量安全**: 请确保 `.env` 文件已添加到 `.gitignore`，不要将敏感信息提交到代码仓库
2. **网络支持**: 目前主要支持 Polygon 主网（chain_id: 137），Amoy 测试网部分功能可能受限
3. **钱包类型**: **目前仅支持 Proxy 代理钱包**（signature_type: 1），Safe 和 EOA 钱包的赎回功能正在开发中
4. **Gas 费用**: 通过 Relayer 执行交易，Gas 费用由 Relayer 处理

## 开发

### 安装开发依赖

```bash
uv pip install -e ".[dev]"
```

### 运行示例

```bash
python examples/example_redeem.py
```

### 贡献

我们欢迎所有形式的贡献！如果您想：

- 实现 Safe 或 EOA 钱包支持
- 修复 bug 或改进现有功能
- 添加新功能或改进文档
- 提出建议或报告问题

请随时提交 Issue 或 Pull Request。您的贡献将帮助这个项目变得更好！

## 许可证

MIT

## 作者

PinBar

## 相关链接

- [Polymarket](https://polymarket.com/)
- [Polygon Network](https://polygon.technology/)

