# -*- coding = utf-8 -*-
# @Time: 2025/12/21 19:44
# @Author: PinBar
# @Site:
# @File: secp256k1.py
# @Software: PyCharm
from eth_keys import keys
from eth_utils import decode_hex

SECP256K1_N = int(
    "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16
)
HALF_N = SECP256K1_N // 2


def sign(hash_hex: str, priv_hex: str):
    msg = decode_hex(hash_hex)
    priv = keys.PrivateKey(decode_hex(priv_hex))
    sig = priv.sign_msg_hash(msg)
    r, s, v = sig.r, sig.s, sig.v

    if s > HALF_N:
        s = SECP256K1_N - s
        # Ethereum recovery id flips when s is negated
        v ^= 1

    return r, s, v


def int_to_hex(n: int, size: int = 32) -> str:
    # size 是字节数，32 字节 -> 64 个 hex 字符
    return "0x" + n.to_bytes(size, "big").hex()


def hex_to_int(h: str) -> int:
    return int(h, 16)


def serialize_signature(r: str, s: str, v=None, yParity=None, to="hex"):
    # 计算 yParity_
    if yParity in (0, 1):
        yParity_ = yParity
    elif v is not None and (v in (27, 28) or v >= 35):
        yParity_ = 1 if (v % 2 == 0) else 0
    else:
        raise ValueError("Invalid `v` or `yParity` value")

    # toCompactHex: r||s (各 32 字节)
    r_int = hex_to_int(r)
    s_int = hex_to_int(s)
    compact = r_int.to_bytes(32, "big").hex() + s_int.to_bytes(32, "big").hex()

    signature_hex = "0x" + compact + ("1b" if yParity_ == 0 else "1c")

    if to == "hex":
        return signature_hex
    return bytes.fromhex(signature_hex[2:])
