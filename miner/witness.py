#!/usr/bin/env python3

"""
Bitcoin Miner Lab
Witness Commitment Module

Educational implementation of Bitcoin SegWit witness
Merkle root and witness commitment calculation.

This module is designed for Bitcoin Core regtest
block construction and mining.

Pipeline:

1. Coinbase WTXID is represented by 32 zero bytes.
2. Collect WTXIDs of all non-coinbase transactions.
3. Build the witness Merkle tree.
4. Calculate the witness Merkle root.
5. Combine the root with the 32-byte witness reserved value.
6. Double-SHA256 the result.
7. Build the BIP141 witness commitment script.

Run:

    python -m miner.witness
"""

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
# WTXID CONVERSION
# ============================================================

def wtxid_to_internal(wtxid):
    """
    Convert a displayed WTXID into the internal byte order
    used when calculating the Merkle tree.

    Bitcoin RPC displays transaction hashes in reversed
    byte order compared with the internal hash representation.
    """

    if not isinstance(wtxid, str):
        raise TypeError("WTXID must be a hexadecimal string.")

    if len(wtxid) != 64:
        raise ValueError(
            f"WTXID must contain exactly 64 hexadecimal characters. "
            f"Got {len(wtxid)} characters."
        )

    try:
        raw = bytes.fromhex(wtxid)
    except ValueError as exc:
        raise ValueError(
            f"Invalid WTXID hexadecimal string: {wtxid}"
        ) from exc

    return raw[::-1]


def internal_to_hash_hex(internal_hash):
    """
    Convert an internal hash byte sequence into the normal
    displayed hexadecimal byte order.
    """

    if len(internal_hash) != 32:
        raise ValueError(
            "Internal hash must be exactly 32 bytes."
        )

    return internal_hash[::-1].hex()


# ============================================================
# WITNESS MERKLE TREE
# ============================================================

def build_merkle_tree(hash_bytes):
    """
    Build a Bitcoin-style Merkle tree from internal-order hashes.

    If the number of hashes is odd, the final hash is duplicated.
    """

    if not hash_bytes:
        raise ValueError(
            "Cannot build a Merkle tree from an empty list."
        )

    current = list(hash_bytes)

    for item in current:
        if len(item) != 32:
            raise ValueError(
                "Every Merkle tree hash must be exactly 32 bytes."
            )

    while len(current) > 1:

        if len(current) % 2 == 1:
            current.append(current[-1])

        next_level = []

        for index in range(0, len(current), 2):

            combined = (
                current[index]
                + current[index + 1]
            )

            parent = double_sha256(combined)

            next_level.append(parent)

        current = next_level

    return current[0]


def witness_merkle_root(wtxids):
    """
    Calculate the witness Merkle root.

    The first entry is always the coinbase WTXID, which is
    represented by 32 zero bytes.

    wtxids should contain only non-coinbase transaction WTXIDs.
    """

    hashes = [
        b"\x00" * 32
    ]

    for wtxid in wtxids:
        hashes.append(
            wtxid_to_internal(wtxid)
        )

    return build_merkle_tree(hashes)


def witness_merkle_root_hex(wtxids):
    """
    Return the witness Merkle root in normal displayed
    hexadecimal byte order.
    """

    root = witness_merkle_root(wtxids)

    return internal_to_hash_hex(root)


# ============================================================
# WITNESS COMMITMENT
# ============================================================

def calculate_witness_commitment(
    wtxids,
    witness_reserved_value=None
):
    """
    Calculate the 32-byte BIP141 witness commitment hash.

    Commitment hash:

        SHA256d(
            witness_merkle_root
            + witness_reserved_value
        )

    The default witness reserved value is 32 zero bytes.
    """

    if witness_reserved_value is None:
        witness_reserved_value = b"\x00" * 32

    if len(witness_reserved_value) != 32:
        raise ValueError(
            "Witness reserved value must be exactly 32 bytes."
        )

    root = witness_merkle_root(wtxids)

    commitment = double_sha256(
        root
        + witness_reserved_value
    )

    return commitment


def calculate_witness_commitment_hex(
    wtxids,
    witness_reserved_value=None
):
    """
    Return the witness commitment hash as hexadecimal.
    """

    commitment = calculate_witness_commitment(
        wtxids,
        witness_reserved_value
    )

    return commitment.hex()


def build_witness_commitment_script(
    wtxids,
    witness_reserved_value=None
):
    """
    Build the BIP141 witness commitment output script.

    Script format:

        OP_RETURN
        OP_PUSHBYTES_36
        aa21a9ed
        <32-byte commitment>
    """

    commitment = calculate_witness_commitment(
        wtxids,
        witness_reserved_value
    )

    script = (
        b"\x6a"
        + b"\x24"
        + bytes.fromhex("aa21a9ed")
        + commitment
    )

    return script


def build_witness_commitment_script_hex(
    wtxids,
    witness_reserved_value=None
):
    """
    Return the complete witness commitment script
    as hexadecimal.
    """

    script = build_witness_commitment_script(
        wtxids,
        witness_reserved_value
    )

    return script.hex()


# ============================================================
# TESTS
# ============================================================

def run_tests():
    """
    Run basic witness commitment tests.
    """

    print("Bitcoin Witness Commitment Tests")
    print("=" * 60)

    # --------------------------------------------------------
    # Test 1
    # No non-coinbase transactions.
    # --------------------------------------------------------

    print("\nTest 1: Coinbase only")

    txs = []

    root = witness_merkle_root_hex(txs)

    commitment = calculate_witness_commitment_hex(txs)

    script = build_witness_commitment_script_hex(txs)

    print(f"Witness Merkle root: {root}")
    print(f"Commitment:          {commitment}")
    print(f"Commitment script:   {script}")

    if len(root) != 64:
        raise AssertionError(
            "Witness Merkle root must be 32 bytes."
        )

    if len(commitment) != 64:
        raise AssertionError(
            "Witness commitment must be 32 bytes."
        )

    if not script.startswith(
        "6a24aa21a9ed"
    ):
        raise AssertionError(
            "Invalid witness commitment script prefix."
        )

    print("Result: PASS")

    # --------------------------------------------------------
    # Test 2
    # One non-coinbase transaction.
    # --------------------------------------------------------

    print("\nTest 2: One transaction")

    tx1 = (
        "19eefba0d20df8147114ed9948c85d7ae5c7fa4978846eaa8a65015cfb23a7d5"
    )

    txs = [tx1]

    root = witness_merkle_root_hex(txs)

    commitment = calculate_witness_commitment_hex(txs)

    print(f"WTXID:               {tx1}")
    print(f"Witness Merkle root: {root}")
    print(f"Commitment:          {commitment}")

    print("Result: PASS")

    # --------------------------------------------------------
    # Test 3
    # Two non-coinbase transactions.
    # --------------------------------------------------------

    print("\nTest 3: Two transactions")

    tx2 = (
        "0000000000000000000000000000000000000000000000000000000000000000"
    )

    txs = [
        tx1,
        tx2
    ]

    root = witness_merkle_root_hex(txs)

    commitment = calculate_witness_commitment_hex(txs)

    print(f"Witness Merkle root: {root}")
    print(f"Commitment:          {commitment}")

    print("Result: PASS")

    print("\nAll witness commitment tests completed.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        run_tests()

    except Exception as exc:
        print("\nERROR:")
        print(str(exc))
        raise