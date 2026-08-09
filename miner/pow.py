#!/usr/bin/env python3

"""
Bitcoin Miner Lab - Proof of Work Module

Provides:

1. Double SHA256 hashing
2. Compact target decoding
3. 80-byte block header serialization
4. Block hash calculation
5. Proof-of-work validation
6. Regtest nonce mining

REGTEST / EDUCATIONAL USE.
"""

import hashlib
import struct
import time


# ============================================================
# HASHING
# ============================================================

def double_sha256(data):

    return hashlib.sha256(
        hashlib.sha256(
            data
        ).digest()
    ).digest()


# ============================================================
# COMPACT TARGET
# ============================================================

def compact_to_target(bits):

    exponent = (
        bits >> 24
    )

    mantissa = (
        bits & 0x007fffff
    )

    if bits & 0x00800000:

        mantissa = (
            -mantissa
        )

    if exponent <= 3:

        return (
            mantissa
            >> (
                8
                * (
                    3
                    - exponent
                )
            )
        )

    return (
        mantissa
        << (
            8
            * (
                exponent
                - 3
            )
        )
    )


# ============================================================
# BLOCK HEADER
# ============================================================

def build_block_header(
    version,
    previous_block_hash,
    merkle_root,
    curtime,
    bits,
    nonce
):

    header = (

        struct.pack(
            "<I",
            version
        )

        + bytes.fromhex(
            previous_block_hash
        )[::-1]

        + merkle_root

        + struct.pack(
            "<I",
            curtime
        )

        + struct.pack(
            "<I",
            bits
        )

        + struct.pack(
            "<I",
            nonce
        )

    )

    if len(header) != 80:

        raise ValueError(
            "Block header must be "
            "exactly 80 bytes"
        )

    return header


# ============================================================
# BLOCK HASH
# ============================================================

def block_hash_from_header(
    header
):

    if len(header) != 80:

        raise ValueError(
            "Block header must be "
            "exactly 80 bytes"
        )

    return (
        double_sha256(
            header
        )[::-1].hex()
    )


# ============================================================
# PROOF OF WORK VALIDATION
# ============================================================

def check_proof_of_work(
    header,
    bits
):

    target = compact_to_target(
        bits
    )

    digest = double_sha256(
        header
    )

    hash_int = int.from_bytes(

        digest,

        byteorder="little"

    )

    return (
        hash_int <= target
    )


# ============================================================
# MINE HEADER
# ============================================================

def mine_header(
    version,
    previous_block_hash,
    merkle_root,
    curtime,
    bits
):

    """
    Search the 32-bit nonce space for a valid
    proof-of-work block header.

    Returns:

        (
            valid_header,
            block_hash
        )

    The block hash is returned in normal
    human-readable big-endian display order.
    """

    target = compact_to_target(
        bits
    )

    if target <= 0:

        raise ValueError(
            "Invalid proof-of-work target."
        )

    print(
        f"Target: "
        f"{target:064x}"
    )

    start_time = time.time()

    nonce = 0

    hashes_done = 0

    while nonce <= 0xffffffff:

        header = build_block_header(

            version,

            previous_block_hash,

            merkle_root,

            curtime,

            bits,

            nonce

        )

        digest = double_sha256(
            header
        )

        hash_int = int.from_bytes(

            digest,

            byteorder="little"

        )

        hashes_done += 1

        if hash_int <= target:

            block_hash = (

                digest[::-1].hex()

            )

            elapsed = (

                time.time()

                - start_time

            )

            print(
                "\n*** VALID PROOF "
                "OF WORK FOUND ***"
            )

            print(
                f"Nonce: {nonce}"
            )

            print(
                f"Block hash: "
                f"{block_hash}"
            )

            print(
                f"Hashes: "
                f"{hashes_done:,}"
            )

            print(
                f"Time: "
                f"{elapsed:.6f} seconds"
            )

            return (

                header,

                block_hash

            )

        nonce += 1

        if (

            nonce % 1_000_000

            == 0

        ):

            print(

                f"\rNonce: "
                f"{nonce:,}",

                end="",

                flush=True

            )

    raise RuntimeError(

        "Nonce space exhausted "
        "without finding valid "
        "proof of work."

    )


# ============================================================
# TESTS
# ============================================================

def run_tests():

    print(
        "Bitcoin Proof-of-Work Tests"
    )

    print(
        "=" * 50
    )

    bits = 0x207fffff

    target = compact_to_target(
        bits
    )

    print(
        "Bits:",
        f"{bits:08x}"
    )

    print(
        "Target:",
        f"{target:064x}"
    )

    assert target > 0

    print(
        "Compact target: PASS"
    )

    header = build_block_header(

        0x20000000,

        "00" * 32,

        b"\x00" * 32,

        1234567890,

        bits,

        0

    )

    print(
        "Header size:",
        len(header),
        "bytes"
    )

    assert len(header) == 80

    print(
        "Header serialization: PASS"
    )

    block_hash = block_hash_from_header(
        header
    )

    print(
        "Block hash:",
        block_hash
    )

    assert len(block_hash) == 64

    print(
        "Block hash calculation: PASS"
    )

    valid = check_proof_of_work(

        header,

        bits

    )

    print(
        "PoW validation result:",
        valid
    )

    print()

    print(
        "All Proof-of-Work tests completed."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_tests()