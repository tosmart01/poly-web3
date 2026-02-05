# poly-web3

![PyPI](https://img.shields.io/pypi/v/poly-web3)
![Python](https://img.shields.io/pypi/pyversions/poly-web3)
![License](https://img.shields.io/github/license/tosmart01/poly-web3)

Polymarket Proxy 与 Safe 钱包赎回操作的 Python SDK，免 gas 费。

[English](README.md) | 中文

```bash
Python >= 3.11
pip install poly-web3
```

```python
from poly_web3 import PolyWeb3Service

service = PolyWeb3Service(
    clob_client=client,
    relayer_client=relayer_client,
)

# 赎回当前账户下所有可赎回仓位
service.redeem_all(batch_size=10)
```

[查看完整示例](#快速开始)

## 赎回说明

- 可赎回仓位通过官方 Positions API 查询，通常有约 1 分钟延迟。
- `redeem_all` 若无可赎回仓位则返回空数组；若返回数组中包含 `None`，表示赎回失败，需要重试。

## FAQ

1. **页面显示可赎回，但 `redeem_all` 返回 `[]`**：官方 Positions API 可能有 1-3 分钟延迟，稍等后重试。
2. **赎回时出现 RPC 报错**：请更换 RPC 节点，在 `PolyWeb3Service` 实例化时设置 `rpc_url`。
3. **赎回状态一直是 `execute`**：官方 relayer 可能拥堵，暂停赎回 1 小时，避免连续提交导致 nonce 循环问题。
4. **Relayer client 返回 403**：需要按官方文档申请 Builder key。Reference / 参考链接：Polymarket Builders — Introduction: https://docs.polymarket.com/developers/builders/builder-intro
5. **Relayer 每日限额**：官方 relayer 通常每日限制 100 次请求，推荐使用批量赎回（`batch_size`）以减少请求次数，避免超额。

## 关于项目

本项目是对Polymarket 官方 TypeScript 实现的 `builder-relayer-client` 的 Python 重写版本，旨在为 Python 开发者提供在 Polymarket 上执行 Proxy 与 Safe 钱包赎回操作的便捷工具。

**重要说明：**
- 本项目**仅实现了官方的 redeem（赎回）功能**，专注于条件代币基金（CTF）的赎回操作
- 其他功能（如交易、下单等）不在本项目的实现范围内


**注意**
本仓库中与 Polymarket 相关的赎回（redeem）或某些写入型操作依赖于 Polymarket 的 Builder 计划权限。要在真实环境中执行赎回操作，你必须先按照 Polymarket 官方的 Builder 申请流程申请并获得相应的 key/权限。请参阅官方文档并完成申请流程后，将获得使用 Builder API 的凭证，才能让本项目的赎回功能正常工作

Reference / 参考链接：
- Polymarket Builders — Introduction: https://docs.polymarket.com/developers/builders/builder-intro

**当前状态：**
- ✅ **Proxy 代理钱包** - 已完全支持 redeem 功能， 免gas费
- ✅ **Safe 钱包** - 已完全支持 redeem 功能
- 🚧 **EOA 钱包** - 开发中

我们欢迎社区贡献！如果您想帮助实现 EOA 钱包的 redeem 功能支持，或者有其他改进建议，欢迎提交 Pull Request。

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
- `web3 >= 7.0.0` - Web3.py 库
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
    signature_type=1,  # Proxy 钱包类型（signature_type=2 Safe）
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
service = PolyWeb3Service(
    clob_client=client,
    relayer_client=relayer_client,
    rpc_url="https://polygon-bor.publicnode.com",  # 可选
)

# 赎回当前账户下所有可赎回仓位
redeem_all_result = service.redeem_all(batch_size=10)
print(f"全部赎回结果: {redeem_all_result}")
# 如果 redeem_all_result 列表中有 None，则表示失败，请参考 README FAQ 后重试
if redeem_all_result and any(item is None for item in redeem_all_result):
    print("部分赎回失败，请重试。")

# 执行赎回操作（批量）
condition_ids = [
    "0xc3df016175463c44f9c9f98bddaa3bf3daaabb14b069fb7869621cffe73ddd1c",
    "0x31fb435a9506d14f00b9de5e5e4491cf2223b6d40a2525d9afa8b620b61b50e2",
]
redeem_batch_result = service.redeem(condition_ids, batch_size=10)
print(f"批量赎回结果: {redeem_batch_result}")
if redeem_all_result and any(item is None for item in redeem_all_result):
    print("部分赎回失败，请重试。")
```

## API 文档

### PolyWeb3Service

主要的服务类，根据钱包类型自动选择合适的服务实现。

#### 方法

##### `redeem(condition_ids: str | list[str], batch_size: int = 20)`

执行赎回操作。

**参数:**
- `condition_ids` (str | list[str]): 条件 ID 或条件 ID 列表
- `batch_size` (int): 每批次处理数量

**返回:**
- `dict | list[dict]`: 交易结果，包含交易状态和相关信息

**示例:**

```python
# 单笔赎回
result = service.redeem("0x...")

# 批量赎回
result = service.redeem(["0x...", "0x..."], batch_size=10)
```

##### `redeem_all(batch_size: int = 20) -> list[dict]`

赎回当前账户下所有可赎回仓位。

**返回:**
- `list[dict]`: 赎回结果列表；若无可赎回仓位则返回空数组；若数组中包含 `None`，表示赎回失败，需要重试

**示例:**

```python
# 赎回所有可赎回仓位
service.redeem_all(batch_size=10)
```

#### 可选 API

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

## 可选：查询操作

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
    └── safe_service.py     # Safe 钱包服务（✅ 已实现）
```

## 注意事项

1. **环境变量安全**: 请确保 `.env` 文件已添加到 `.gitignore`，不要将敏感信息提交到代码仓库
2. **网络支持**: 目前主要支持 Polygon 主网（chain_id: 137），Amoy 测试网部分功能可能受限
3. **钱包类型**: 已支持 Proxy（signature_type: 1）和 Safe（signature_type: 2），EOA 钱包赎回功能仍在开发中
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

最简单的贡献流程：

1. 先提 Issue 说明问题或需求。
2. Fork 并新建分支：`feat/xxx` 或 `fix/xxx`。
3. 完成修改，必要时同步更新文档。
4. 运行：`uv run python -m examples.example_redeem`（如果适用）。
5. 提交 PR 并关联对应 Issue。

## 许可证

MIT

## 作者

PinBar

## 相关链接

- [Polymarket](https://polymarket.com/)
- [Polygon Network](https://polygon.technology/)
