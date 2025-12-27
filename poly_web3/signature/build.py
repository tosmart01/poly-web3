# -*- coding = utf-8 -*-
# @Time: 2025/12/21 19:45
# @Author: PinBar
# @Site:
# @File: build.py
# @Software: PyCharm
from typing import Union, Optional


def string_to_bytes(value: str, size: Optional[int] = None) -> bytes:
    data = value.encode("utf-8")
    if size is None:
        return data
    if len(data) > size:
        raise ValueError(f"Size overflow: given {len(data)}, max {size}")
    return data + b"\x00" * (size - len(data))


def keccak256(data: bytes) -> bytes:
    try:
        from eth_hash.auto import keccak

        return keccak(data)
    except Exception:
        try:
            import sha3  # pysha3

            k = sha3.keccak_256()
        except Exception:
            from Crypto.Hash import keccak  # pycryptodome

            k = keccak.new(digest_bits=256)
        k.update(data)
        return k.digest()


def to_checksum_address(addr_bytes: bytes) -> str:
    hex_addr = addr_bytes.hex()
    hash_hex = keccak256(hex_addr.encode()).hex()
    checksum = "".join(
        ch.upper() if int(hash_hex[i], 16) >= 8 else ch for i, ch in enumerate(hex_addr)
    )
    return "0x" + checksum


def derive_proxy_wallet(address: str, proxy_factory: str, bytecode_hash: str) -> str:
    addr_bytes = bytes.fromhex(address[2:] if address.startswith("0x") else address)
    factory_bytes = bytes.fromhex(
        proxy_factory[2:] if proxy_factory.startswith("0x") else proxy_factory
    )
    bytecode_bytes = bytes.fromhex(
        bytecode_hash[2:] if bytecode_hash.startswith("0x") else bytecode_hash
    )
    salt = keccak256(
        addr_bytes
    )  # equivalent to keccak256(encodePacked(["address"], [address]))
    data = b"\xff" + factory_bytes + salt + bytecode_bytes
    create2_hash = keccak256(data)
    return to_checksum_address(create2_hash[12:])  # last 20 bytes


HexLike = Union[str, bytes, int]


def create_struct_hash(
    from_addr: str,
    to: str,
    data: str,
    tx_fee: HexLike,
    gas_price: HexLike,
    gas_limit: HexLike,
    nonce: HexLike,
    relay_hub_address: str,
    relay_address: str,
) -> str:
    def to_bytes(hex_like: HexLike, size: int | None = None) -> bytes:
        if isinstance(hex_like, int):
            length = (
                size if size is not None else max(1, (hex_like.bit_length() + 7) // 8)
            )
            return hex_like.to_bytes(length, "big")
        if isinstance(hex_like, bytes):
            return hex_like.rjust(size, b"\x00") if size else hex_like
        if isinstance(hex_like, str):
            if hex_like.startswith("0x"):
                raw = bytes.fromhex(hex_like[2:])
                return raw.rjust(size, b"\x00") if size else raw
            if hex_like.isdigit():  # numeric string -> int
                num = int(hex_like)
                length = (
                    size if size is not None else max(1, (num.bit_length() + 7) // 8)
                )
                return num.to_bytes(length, "big")
            raw = hex_like.encode()  # fallback ascii
            return raw.rjust(size, b"\x00") if size else raw
        raise TypeError("Unsupported type for to_bytes")

    relay_hub_prefix = to_bytes("rlx:")
    data_to_hash = b"".join(
        [
            relay_hub_prefix,
            to_bytes(from_addr),
            to_bytes(to),
            to_bytes(data),
            to_bytes(tx_fee, size=32),
            to_bytes(gas_price, size=32),
            to_bytes(gas_limit, size=32),
            to_bytes(nonce, size=32),
            to_bytes(relay_hub_address),
            to_bytes(relay_address),
        ]
    )
    return "0x" + keccak256(data_to_hash).hex()
