#!/usr/bin/env python3

"""
Bitcoin Miner Lab
Coinbase Transaction Module

Educational Bitcoin Regtest coinbase transaction builder.

This module handles:

1. BIP34 block-height encoding.
2. Coinbase scriptSig construction.
3. Coinbase input serialization.
4. Mining reward output.
5. SegWit witness commitment output.
6. Coinbase witness reserved value.
7. SegWit coinbase serialization.
8. Coinbase TXID calculation.

REGTEST / EDUCATIONAL USE.
"""

import struct
import time
import hashlib


# ============================================================
# HASHING
# ============================================================

def sha256(data):
    """Return a single SHA256 hash."""
    return hashlib.sha256(data).digest()


def double_sha256(data):
    """Return SHA256(SHA256(data))."""
    return sha256(sha256(data))


# ============================================================
# SERIALIZATION
# ============================================================

def encode_varint(n):
    """
    Encode an integer using Bitcoin CompactSize format.
    """

    if n < 0xfd:
        return struct.pack("<B", n)

    if n <= 0xffff:
        return (
            b"\xfd"
            + struct.pack("<H", n)
        )

    if n <= 0xffffffff:
        return (
            b"\xfe"
            + struct.pack("<I", n)
        )

    return (
        b"\xff"
        + struct.pack("<Q", n)
    )


def encode_script_number(n):
    """
    Encode an integer using Bitcoin Script's
    minimally encoded signed-magnitude format.
    """

    if n == 0:
        return b""

    negative = n < 0

    if negative:
        n = -n

    result = bytearray()

    while n:
        result.append(n & 0xff)
        n >>= 8

    if result[-1] & 0x80:

        result.append(
            0x80 if negative else 0x00
        )

    elif negative:

        result[-1] |= 0x80

    return bytes(result)


def push_data(data):
    """
    Encode a data push for Bitcoin Script.
    """

    length = len(data)

    if length < 0x4c:

        return (
            bytes([length])
            + data
        )

    if length <= 0xff:

        return (
            b"\x4c"
            + bytes([length])
            + data
        )

    if length <= 0xffff:

        return (
            b"\x4d"
            + struct.pack("<H", length)
            + data
        )

    return (
        b"\x4e"
        + struct.pack("<I", length)
        + data
    )


# ============================================================
# BIP34 BLOCK HEIGHT
# ============================================================

def build_coinbase_height_prefix(height):
    """
    Build the first script element of the coinbase scriptSig.

    BIP34 requires the block height to be the first
    item in the coinbase scriptSig.
    """

    height_data = encode_script_number(height)

    return push_data(height_data)


def validate_coinbase_height(
    script_sig,
    expected_height
):
    """
    Verify that the first scriptSig element contains
    the expected BIP34 block height.
    """

    expected_prefix = (
        build_coinbase_height_prefix(
            expected_height
        )
    )

    actual_prefix = (
        script_sig[
            :len(expected_prefix)
        ]
    )

    if actual_prefix != expected_prefix:

        raise ValueError(
            "BIP34 coinbase height validation failed.\n"
            f"Expected: {expected_prefix.hex()}\n"
            f"Actual:   {actual_prefix.hex()}"
        )

    return True


# ============================================================
# COINBASE TRANSACTION BUILDER
# ============================================================

def build_coinbase(
    height,
    coinbase_value,
    script_pubkey,
    witness_commitment,
    extra_data=b"Bitcoin-Miner-Lab"
):
    """
    Build a complete SegWit coinbase transaction.

    Parameters:

        height:
            Block height.

        coinbase_value:
            Block subsidy + transaction fees, in satoshis.

        script_pubkey:
            Script where the mining reward is paid.

        witness_commitment:
            32-byte witness commitment hash.

        extra_data:
            Additional coinbase scriptSig data.

    Returns:

        Dictionary containing:

            tx:
                Complete SegWit coinbase transaction.

            txid:
                Coinbase TXID.

            witness_reserved_value:
                32-byte reserved value.

            script_sig:
                Coinbase scriptSig.

            witness_commitment_script:
                Witness commitment output script.
    """

    if height < 0:
        raise ValueError(
            "Block height cannot be negative."
        )

    if coinbase_value < 0:
        raise ValueError(
            "Coinbase value cannot be negative."
        )

    if len(script_pubkey) == 0:
        raise ValueError(
            "scriptPubKey cannot be empty."
        )

    if len(witness_commitment) != 32:
        raise ValueError(
            "Witness commitment must be exactly 32 bytes."
        )

    # --------------------------------------------------------
    # BIP34 block height
    # --------------------------------------------------------

    height_prefix = (
        build_coinbase_height_prefix(
            height
        )
    )

    # --------------------------------------------------------
    # Extra coinbase data
    # --------------------------------------------------------

    timestamp = struct.pack(
        "<I",
        int(time.time()) & 0xffffffff
    )

    script_sig = (
        height_prefix
        + extra_data
        + timestamp
    )

    # Coinbase scriptSig must be 2-100 bytes.
    if len(script_sig) < 2:

        script_sig += (
            b"\x00"
            * (2 - len(script_sig))
        )

    if len(script_sig) > 100:

        raise ValueError(
            "Coinbase scriptSig exceeds 100 bytes."
        )

    # Verify BIP34 height.
    validate_coinbase_height(
        script_sig,
        height
    )

    # --------------------------------------------------------
    # Coinbase input
    # --------------------------------------------------------

    coinbase_input = (

        b"\x00" * 32

        + struct.pack(
            "<I",
            0xffffffff
        )

        + encode_varint(
            len(script_sig)
        )

        + script_sig

        + struct.pack(
            "<I",
            0xffffffff
        )
    )

    # --------------------------------------------------------
    # Mining reward output
    # --------------------------------------------------------

    reward_output = (

        struct.pack(
            "<Q",
            coinbase_value
        )

        + encode_varint(
            len(script_pubkey)
        )

        + script_pubkey
    )

    # --------------------------------------------------------
    # Witness commitment output
    # --------------------------------------------------------

    witness_commitment_script = (

        b"\x6a"
        + b"\x24"
        + bytes.fromhex(
            "aa21a9ed"
        )
        + witness_commitment
    )

    commitment_output = (

        struct.pack(
            "<Q",
            0
        )

        + encode_varint(
            len(witness_commitment_script)
        )

        + witness_commitment_script
    )

    # --------------------------------------------------------
    # Outputs
    # --------------------------------------------------------

    outputs = (

        reward_output
        + commitment_output
    )

    # --------------------------------------------------------
    # Transaction version
    # --------------------------------------------------------

    version = struct.pack(
        "<I",
        2
    )

    input_count = encode_varint(1)

    output_count = encode_varint(2)

    locktime = struct.pack(
        "<I",
        0
    )

    # --------------------------------------------------------
    # Non-witness serialization
    #
    # This serialization is used to calculate the TXID.
    # --------------------------------------------------------

    non_witness_tx = (

        version

        + input_count

        + coinbase_input

        + output_count

        + outputs

        + locktime
    )

    # --------------------------------------------------------
    # Coinbase witness
    #
    # Exactly one 32-byte witness reserved value.
    # --------------------------------------------------------

    witness_reserved_value = (
        b"\x00" * 32
    )

    witness = (

        encode_varint(1)

        + encode_varint(32)

        + witness_reserved_value
    )

    # --------------------------------------------------------
    # Complete SegWit transaction
    # --------------------------------------------------------

    segwit_tx = (

        version

        + b"\x00\x01"

        + input_count

        + coinbase_input

        + output_count

        + outputs

        + witness

        + locktime
    )

    # --------------------------------------------------------
    # Calculate TXID
    #
    # TXID is calculated from the non-witness serialization.
    # --------------------------------------------------------

    txid_internal = double_sha256(
        non_witness_tx
    )

    txid = (
        txid_internal[::-1].hex()
    )

    return {

        "tx": segwit_tx,

        "txid": txid,

        "witness_reserved_value":
            witness_reserved_value,

        "script_sig":
            script_sig,

        "witness_commitment_script":
            witness_commitment_script

    }


# ============================================================
# TESTS
# ============================================================

def run_tests():
    """
    Run standalone coinbase transaction tests.
    """

    print(
        "Bitcoin Coinbase Transaction Tests"
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # Test configuration
    # --------------------------------------------------------

    height = 105

    coinbase_value = 5000010000

    # Example P2WPKH scriptPubKey.
    #
    # This is only a test script.
    # It is not generated from a wallet address here.

    script_pubkey = bytes.fromhex(
        "00146353b04f94388932356774e1b9813f00be727643"
    )

    witness_commitment = bytes.fromhex(
        "5f523db356f2e3c74ab84fe8258beb5ea52ca2f7312d7dfb05d2f9be64d0aab1"
    )

    # --------------------------------------------------------
    # Build coinbase
    # --------------------------------------------------------

    result = build_coinbase(

        height=height,

        coinbase_value=coinbase_value,

        script_pubkey=script_pubkey,

        witness_commitment=witness_commitment
    )

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print(
        f"\nBlock height: "
        f"{height}"
    )

    print(
        f"Coinbase value: "
        f"{coinbase_value} satoshis"
    )

    print(
        f"Coinbase scriptSig: "
        f"{result['script_sig'].hex()}"
    )

    print(
        f"Coinbase TXID: "
        f"{result['txid']}"
    )

    print(
        f"Witness reserved value: "
        f"{result['witness_reserved_value'].hex()}"
    )

    print(
        f"Witness commitment script: "
        f"{result['witness_commitment_script'].hex()}"
    )

    print(
        f"Serialized coinbase size: "
        f"{len(result['tx'])} bytes"
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    assert validate_coinbase_height(
        result["script_sig"],
        height
    )

    assert len(
        result["witness_reserved_value"]
    ) == 32

    assert len(
        result["witness_commitment_script"]
    ) == 38

    assert len(
        result["tx"]
    ) > 0

    print(
        "\nBIP34 height check: PASS"
    )

    print(
        "Witness reserved value check: PASS"
    )

    print(
        "Witness commitment script check: PASS"
    )

    print(
        "Coinbase serialization check: PASS"
    )

    print(
        "\nAll coinbase tests completed."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        run_tests()

    except Exception as exc:

        print(
            "\nERROR:"
        )

        print(
            str(exc)
        )

        raise