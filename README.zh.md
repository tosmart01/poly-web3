# poly-web3

![PyPI](https://img.shields.io/pypi/v/poly-web3)
![Python](https://img.shields.io/pypi/pyversions/poly-web3)
![License](https://img.shields.io/github/license/tosmart01/poly-web3)

Polymarket Proxy 与 Safe 钱包赎回与拆分/合并仓位的 Python SDK，免 gas 费。当前版本已支持 Polymarket CLOB v2，并使用 `py-clob-client-v2`。

[English](README.md) | 中文

可选支持地址分析（手续费影响与盈亏曲线），见 [地址分析（可选）](#地址分析可选)。

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
# 指定 condition_ids 赎回
service.redeem(condition_ids=["0x..."])

# Split/Merge for binary markets (amount in human pUSD units).
service.split("0x...", 10)
service.merge("0x...", 10)
# merge 所有仓位
service.merge_all(min_usdc=1, batch_size=10)

# 批量 Split/Merge
service.split_batch([{"condition_id": "", "amount": 10}])
service.merge_batch([{"condition_id": "", "amount": 10}])
```

[查看完整示例](#快速开始)

## 赎回说明

- 可赎回仓位通过官方 Positions API 查询，通常有约 1 分钟延迟。
- `redeem` 和 `redeem_all` 现在都返回 `RedeemResult` 这个 pydantic 对象，包含 `success_list` 和 `error_list`。
- `success_list` 保留原始 relayer `execute` 返回结构；`error_list` 会带上 `condition_id`、`market_slug` 和 `error`，方便回溯和重试。
- `error_condition_ids` 是从 `error_list` 派生出的快捷重试列表，可直接 `service.redeem(result.error_condition_ids)`。
- 普通非 negative-risk 市场的 redeem 已按 CLOB v2 pUSD 流程更新；negative-risk redeem 代码路径已保留，但还没有经过真实 Polymarket negative-risk 赎回测试。

## 拆分/合并说明

- `split`/`merge` 适用于二元市场（Yes/No），内部使用默认分区。
- 负风险市场会通过官方 Gamma markets API 自动识别，并路由到 NegRisk Adapter。
- `split`/`merge` 会通过 Polymarket v2 CTF collateral adapter 执行：入参金额使用 pUSD，人类单位；最终生成的 CTF tokenId 会匹配市场 `clobTokenIds`。

## FAQ

1. **页面显示可赎回，但 `redeem_all` 返回 `[]`**：官方 Positions API 可能有 1-3 分钟延迟，稍等后重试。
2. **赎回时出现 RPC 报错**：请更换 RPC 节点，在 `PolyWeb3Service` 实例化时设置 `rpc_url`。
3. **赎回状态一直是 `execute`**：官方 relayer 可能拥堵，暂停赎回 1 小时，避免连续提交导致 nonce 循环问题。
4. **Relayer client 返回 403**：需要按官方文档申请 Builder key。Reference / 参考链接：Polymarket Builders — Introduction: https://docs.polymarket.com/developers/builders/builder-intro
5. **Relayer 每日限额**：官方 relayer 通常每日限制 100 次请求，推荐使用批量赎回（`batch_size`）以减少请求次数，避免超额。

## 关于项目

本项目是对Polymarket 官方 TypeScript 实现的 `builder-relayer-client` 的 Python 重写版本，旨在为 Python 开发者提供在 Polymarket 上执行 Proxy 与 Safe 钱包赎回操作的便捷工具。

**重要说明：**
- 本项目实现了官方的 redeem（赎回）以及二元市场的 split/merge 操作
- 其他功能（如交易、下单等）不在本项目的实现范围内


**注意**
本仓库中与 Polymarket 相关的赎回（redeem）或某些写入型操作依赖于 Polymarket 的 Builder 计划权限。要在真实环境中执行赎回操作，你必须先按照 Polymarket 官方的 Builder 申请流程申请并获得相应的 key/权限。请参阅官方文档并完成申请流程后，将获得使用 Builder API 的凭证，才能让本项目的赎回功能正常工作

Reference / 参考链接：
- Polymarket Builders — Introduction: https://docs.polymarket.com/developers/builders/builder-intro

**当前状态：**
- ✅ **Proxy 代理钱包** - 已完全支持 redeem/split/merge
- ✅ **Safe 钱包** - 已完全支持 redeem/split/merge
- ✅ **Polymarket CLOB v2** - 已通过 `py-clob-client-v2` 支持
- ⚠️ **Negative-risk redeem** - 代码路径已存在，但还没有经过真实 negative-risk redeem 测试
- 🚧 **EOA 钱包** - 开发中

我们欢迎社区贡献！如果您想帮助实现 EOA 钱包相关功能支持，或者有其他改进建议，欢迎提交 Pull Request。

## 安装

```bash
pip install poly-web3
```

或者使用 uv：

```bash
uv add poly-web3
```

安装分析能力（extra）：

```bash
pip install "poly-web3[analysis]"
```

## 环境要求

- Python >= 3.11

## 依赖项

- `py-clob-client-v2 >= 1.0.0` - Polymarket CLOB v2 客户端
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

### 基本使用 - 拆分/合并

```python
import os
import dotenv
from py_builder_relayer_client.client import RelayClient
from py_builder_signing_sdk.config import BuilderConfig
from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds
from py_clob_client_v2 import ClobClient
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

client.set_api_creds(client.create_or_derive_api_key())

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

### 地址分析（可选）

安装 `poly-web3[analysis]` 后，可直接对地址进行：
- 手续费影响分析（`Net PnL` vs `No-Fee PnL`）
- 盈亏曲线与收益比率指标可视化

![盈亏曲线](assets/pnl.png)
![比率指标](assets/ratio.png)

#### 地址分析命令行

安装 `poly-web3[analysis]` 后可直接执行：

```bash
analysis-poly-open --address 0xabc --symbols btc,eth --intervals 5,15
```

或者启动基础服务：

```bash
analysis-poly
```

## API 文档

### PolyWeb3Service

主要的服务类，根据钱包类型自动选择合适的服务实现。

#### 方法

##### `redeem(condition_ids: str | list[str], batch_size: int = 20, collateral_token: str = CTF_COLLATERAL_TOKEN, wrap_redeemed_collateral: bool = True) -> RedeemResult`

执行赎回操作。对于显式传入的 `condition_ids`，如果 Polymarket Positions API 没有返回仓位，服务会回退到链上 CTF 余额检查，支持非 negative-risk 市场。默认会在能从链上计算 payout 时，把 redeem 得到的 USDC.e 在同一笔 relayed transaction 里 wrap 回 pUSD。

**参数:**
- `condition_ids` (str | list[str]): 条件 ID 或条件 ID 列表
- `batch_size` (int): 每批次处理数量
- `collateral_token` (str): 链上 fallback 使用的 CTF 抵押币地址，默认 USDC.e
- `wrap_redeemed_collateral` (bool): 尽可能把 redeem 得到的 USDC.e 自动 wrap 回 pUSD

**返回:**
- `RedeemResult`: pydantic 结果对象，包含：
- `success_list`: 成功批次的原始 relayer `execute` 返回结果
- `error_list`: 失败条目列表，包含 `condition_id`、`market_slug` 和 `error`
- `error_condition_ids`: 从 `error_list` 派生出的快捷重试 condition id 列表

**示例:**

```python
# 单笔赎回
result = service.redeem("0x...")

# 批量赎回
result = service.redeem(["0x...", "0x..."], batch_size=10)
```

##### `redeem_all(batch_size: int = 20) -> RedeemResult`

赎回当前账户下所有可赎回仓位。

**返回:**
- `RedeemResult`: 若无可赎回仓位，则 `success_list` / `error_list` 都为空；部分失败会显式出现在 `error_list` 中，不再返回 `None`

**示例:**

```python
# 赎回所有可赎回仓位
service.redeem_all(batch_size=10)
```

完整赎回示例见 [`examples/example_redeem.py`](examples/example_redeem.py)。

##### `split(condition_id: str, amount: int | float | str, negative_risk: bool | None = None)`

拆分二元市场（Yes/No）仓位，`amount` 为 pUSD 人类单位。

**参数:**
- `condition_id` (str): 条件 ID
- `amount` (int | float | str): pUSD 数量
- `negative_risk` (bool | None): 可选的市场类型提示。为 `None` 时，SDK 会通过官方 Gamma markets API 自动识别，并将负风险市场路由到 NegRisk Adapter。

**返回:**
- `dict | None`: 交易结果

**示例:**

```python
result = service.split("0x...", 1.25)
```

##### `merge(condition_id: str, amount: int | float | str, negative_risk: bool | None = None)`

合并二元市场（Yes/No）仓位，`amount` 为 pUSD 人类单位。

**参数:**
- `condition_id` (str): 条件 ID
- `amount` (int | float | str): pUSD 数量
- `negative_risk` (bool | None): 可选的市场类型提示。为 `None` 时，SDK 会通过官方 Gamma markets API 自动识别，并将负风险市场路由到 NegRisk Adapter。

**返回:**
- `dict | None`: 交易结果

**示例:**

```python
result = service.merge("0x...", 1.25)
```

##### `plan_merge_all(min_usdc: int | float | str = 5, exclude_neg_risk: bool = True) -> list[MergePlanItem]`

扫描当前持仓，计算所有可合并机会，但不发送交易。

**返回:**
- `list[MergePlanItem]`: 每项包含 `condition_id`、`market_slug`、`yes_balance`、`no_balance`、`mergeable`、`negative_risk`、`reason`

**示例:**

```python
plan = service.plan_merge_all(min_usdc=5, exclude_neg_risk=True)
```

##### `merge_all(min_usdc: int | float | str = 5, exclude_neg_risk: bool = True, max_markets: int = 20, batch_size: int = 10) -> MergeAllResult`

批量规划并按需执行合并操作。

**参数:**
- `min_usdc` (int | float | str): 小于该可合并金额的市场会被跳过
- `exclude_neg_risk` (bool): 第一版批量合并流程中是否跳过 neg-risk 市场
- `max_markets` (int): 单次最多执行的市场数量
- `batch_size` (int): 分组后每批最多提交的 merge 交易数量

**返回:**
- `MergeAllResult`: 包含 `plan_list`、`success_list`、`error_list` 和 `error_condition_ids`

**示例:**

```python
result = service.merge_all(
    min_usdc=5,
    exclude_neg_risk=True,
    max_markets=20,
    batch_size=10,
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
    └── safe_service.py     # Safe 钱包服务（✅ 已实现）
```

## 注意事项

1. **环境变量安全**: 请确保 `.env` 文件已添加到 `.gitignore`，不要将敏感信息提交到代码仓库
2. **网络支持**: 目前主要支持 Polygon 主网（chain_id: 137），Amoy 测试网部分功能可能受限
3. **钱包类型**: 已支持 Proxy（signature_type: 1）和 Safe（signature_type: 2），EOA 钱包相关功能仍在开发中
4. **Gas 费用**: 通过 Relayer 执行交易，Gas 费用由 Relayer 处理

## 开发

### 安装开发依赖

```bash
uv pip install -e ".[dev]"
```

### 运行示例

```bash
python examples/example_redeem.py
python examples/example_split_merge.py
```

### 贡献

最简单的贡献流程：

1. 先提 Issue 说明问题或需求。
2. Fork 并新建分支：`feat/xxx` 或 `fix/xxx`。
3. 完成修改，必要时同步更新文档。
4. 运行：`uv run python -m examples.example_redeem` 或 `uv run python -m examples.example_split_merge`（如果适用）。
5. 提交 PR 并关联对应 Issue。

## 许可证

MIT

## 作者

PinBar

## 相关链接

- [Polymarket](https://polymarket.com/)
- [Polygon Network](https://polygon.technology/)
