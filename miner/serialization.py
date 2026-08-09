#!/usr/bin/env python3

"""
Bitcoin Developer Miner
Serialization Module

Low-level Bitcoin serialization helpers.

These functions are used for:

- Transaction serialization
- Coinbase construction
- Block construction
- Bitcoin script data pushes
- Compact integer encoding
- Script number encoding
- SHA-256 hashing
"""

import hashlib
import struct


# ============================================================
# HASHING
# ============================================================

def sha256(data):
    """
    Perform a single SHA-256 hash.

    Returns:
        32-byte hash in internal byte order.
    """

    return hashlib.sha256(
        data
    ).digest()


def double_sha256(data):
    """
    Perform Bitcoin's HASH256 operation.

    HASH256(data) =
        SHA256(SHA256(data))

    Returns:
        32-byte hash in internal byte order.
    """

    return sha256(
        sha256(data)
    )


# ============================================================
# COMPACT SIZE / VARINT
# ============================================================

def encode_varint(n):
    """
    Encode an integer using Bitcoin CompactSize format.

    Examples:

        0xfc
        -> 1 byte

        0xfd
        -> fd + uint16

        0xffff
        -> fd + uint16

        0x10000
        -> fe + uint32
    """

    if n < 0:

        raise ValueError(
            "CompactSize integer "
            "cannot be negative."
        )

    if n < 0xfd:

        return struct.pack(
            "<B",
            n
        )

    if n <= 0xffff:

        return (

            b"\xfd"

            + struct.pack(
                "<H",
                n
            )
        )

    if n <= 0xffffffff:

        return (

            b"\xfe"

            + struct.pack(
                "<I",
                n
            )
        )

    if n <= 0xffffffffffffffff:

        return (

            b"\xff"

            + struct.pack(
                "<Q",
                n
            )
        )

    raise ValueError(
        "Integer is too large "
        "for CompactSize."
    )


# ============================================================
# SCRIPT NUMBER
# ============================================================

def encode_script_number(n):
    """
    Encode an integer using Bitcoin Script's
    minimally encoded signed-magnitude format.

    This is used for values such as the
    block height in a coinbase scriptSig.
    """

    if n == 0:

        return b""

    negative = n < 0

    if negative:

        n = -n

    result = bytearray()

    while n:

        result.append(
            n & 0xff
        )

        n >>= 8

    # If the most significant byte has its
    # sign bit set, append an extra byte.
    if result[-1] & 0x80:

        result.append(

            0x80
            if negative
            else 0x00

        )

    elif negative:

        result[-1] |= 0x80

    return bytes(
        result
    )


# ============================================================
# SCRIPT DATA PUSH
# ============================================================

def push_data(data):
    """
    Serialize a byte string as a Bitcoin Script
    data-push operation.

    This automatically selects:

    - Direct push
    - OP_PUSHDATA1
    - OP_PUSHDATA2
    - OP_PUSHDATA4
    """

    length = len(data)

    # --------------------------------------------------------
    # Direct push
    # --------------------------------------------------------

    if length < 0x4c:

        return (

            bytes([length])

            + data

        )

    # --------------------------------------------------------
    # OP_PUSHDATA1
    # --------------------------------------------------------

    if length <= 0xff:

        return (

            b"\x4c"

            + bytes([length])

            + data

        )

    # --------------------------------------------------------
    # OP_PUSHDATA2
    # --------------------------------------------------------

    if length <= 0xffff:

        return (

            b"\x4d"

            + struct.pack(
                "<H",
                length
            )

            + data

        )

    # --------------------------------------------------------
    # OP_PUSHDATA4
    # --------------------------------------------------------

    if length <= 0xffffffff:

        return (

            b"\x4e"

            + struct.pack(
                "<I",
                length
            )

            + data

        )

    raise ValueError(
        "Data is too large "
        "for OP_PUSHDATA4."
    )


# ============================================================
# TESTS
# ============================================================

def run_tests():
    """
    Run basic serialization tests.
    """

    print(
        "Bitcoin Serialization Tests"
    )

    print(
        "=" * 50
    )

    # --------------------------------------------------------
    # SHA-256
    # --------------------------------------------------------

    test_data = b"hello"

    single_hash = sha256(
        test_data
    )

    double_hash = double_sha256(
        test_data
    )

    print(
        f"SHA256('hello'):\n"
        f"{single_hash.hex()}"
    )

    print(
        f"\nDouble SHA256('hello'):\n"
        f"{double_hash.hex()}"
    )

    # --------------------------------------------------------
    # CompactSize
    # --------------------------------------------------------

    test_values = [

        0,

        1,

        252,

        253,

        255,

        256,

        65535,

        65536,

    ]

    print(
        "\nCompactSize Tests:"
    )

    for value in test_values:

        encoded = encode_varint(
            value
        )

        print(

            f"{value:>6} -> "
            f"{encoded.hex()}"

        )

    # --------------------------------------------------------
    # Script numbers
    # --------------------------------------------------------

    script_values = [

        0,

        1,

        16,

        127,

        128,

        255,

        256,

    ]

    print(
        "\nScript Number Tests:"
    )

    for value in script_values:

        encoded = encode_script_number(
            value
        )

        print(

            f"{value:>6} -> "
            f"{encoded.hex()}"

        )

    # --------------------------------------------------------
    # Push data
    # --------------------------------------------------------

    print(
        "\nPush Data Tests:"
    )

    for data in [

        b"",

        b"A",

        b"Hello",

    ]:

        encoded = push_data(
            data
        )

        print(

            f"{data!r} -> "
            f"{encoded.hex()}"

        )

    print(
        "\nAll serialization tests completed."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_tests()