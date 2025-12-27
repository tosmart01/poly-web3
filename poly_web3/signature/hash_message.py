# -*- coding = utf-8 -*-
# @Time: 2025/12/21 19:43
# @Author: PinBar
# @Site:
# @File: hash_message.py
# @Software: PyCharm
from eth_hash.auto import keccak


def _is_hex(s: str) -> bool:
    return isinstance(s, str) and s.startswith("0x")


def _hex_to_bytes(h: str) -> bytes:
    # 假设是 0x 前缀
    return bytes.fromhex(h[2:])


def _size_of_message(value) -> int:
    # 对齐 viem: hex -> (len-2)/2 向上取整, bytes -> len
    if _is_hex(value):
        return (len(value) - 2 + 1) // 2
    return len(value)


def _to_prefixed_message(message) -> bytes:
    if isinstance(message, str):
        msg_bytes = message.encode("utf-8")
    elif isinstance(message, dict) and "raw" in message:
        raw = message["raw"]
        if isinstance(raw, str):
            # viem 这里直接当作 hex 字符串使用
            msg_bytes = _hex_to_bytes(raw)
        else:
            # raw 可以是 list[int], bytes, bytearray
            msg_bytes = bytes(raw)
    else:
        raise TypeError("Unsupported SignableMessage")

    prefix = f"\x19Ethereum Signed Message:\n{len(msg_bytes)}".encode("utf-8")
    return prefix + msg_bytes


def hash_message(message, to: str = "hex"):
    digest = keccak(_to_prefixed_message(message))
    if to == "bytes":
        return digest
    return "0x" + digest.hex()
