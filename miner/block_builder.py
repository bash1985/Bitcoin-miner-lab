#!/usr/bin/env python3

"""
Bitcoin Miner Lab - Block Builder

Builds a complete Bitcoin block from:

- 80-byte block header
- CompactSize transaction count
- Coinbase transaction
- Regular transactions

This module does not:
- connect to Bitcoin Core
- mine Proof-of-Work
- submit blocks

Those responsibilities belong to other modules.

Regtest-focused educational implementation.
"""

import struct


# ============================================================
# SERIALIZATION HELPERS
# ============================================================

def encode_varint(value):
    """
    Encode an integer using Bitcoin CompactSize format.
    """

    if value < 0:
        raise ValueError("CompactSize value cannot be negative.")

    if value < 0xFD:
        return struct.pack("<B", value)

    if value <= 0xFFFF:
        return (
            b"\xFD"
            + struct.pack("<H", value)
        )

    if value <= 0xFFFFFFFF:
        return (
            b"\xFE"
            + struct.pack("<I", value)
        )

    if value <= 0xFFFFFFFFFFFFFFFF:
        return (
            b"\xFF"
            + struct.pack("<Q", value)
        )

    raise ValueError(
        "CompactSize value is too large."
    )


# ============================================================
# BLOCK ASSEMBLY
# ============================================================

def build_block(
    header,
    coinbase_tx,
    transactions
):
    """
    Assemble a complete serialized Bitcoin block.

    Parameters
    ----------
    header : bytes
        Exactly 80 bytes.

    coinbase_tx : bytes
        Serialized coinbase transaction.

    transactions : list[bytes]
        Serialized non-coinbase transactions.

    Returns
    -------
    bytes
        Complete serialized block.
    """

    if not isinstance(header, bytes):
        raise TypeError(
            "header must be bytes."
        )

    if len(header) != 80:
        raise ValueError(
            f"Block header must be 80 bytes, "
            f"got {len(header)}."
        )

    if not isinstance(coinbase_tx, bytes):
        raise TypeError(
            "coinbase_tx must be bytes."
        )

    if not isinstance(transactions, list):
        raise TypeError(
            "transactions must be a list."
        )

    for tx in transactions:

        if not isinstance(tx, bytes):
            raise TypeError(
                "Every transaction must be bytes."
            )

    all_transactions = [

        coinbase_tx

    ] + transactions

    transaction_count = len(
        all_transactions
    )

    if transaction_count == 0:
        raise ValueError(
            "A block must contain at least "
            "one transaction."
        )

    serialized_block = (

        header

        + encode_varint(
            transaction_count
        )

    )

    for tx in all_transactions:

        serialized_block += tx

    return serialized_block


# ============================================================
# BLOCK VALIDATION HELPERS
# ============================================================

def validate_block_structure(
    block
):
    """
    Perform basic structural validation
    of a serialized Bitcoin block.

    This function checks:

    - Header is present.
    - Header is exactly 80 bytes.
    - Transaction count is present.
    - Transaction count is greater than zero.

    It does not fully parse every transaction.
    """

    if not isinstance(block, bytes):
        raise TypeError(
            "block must be bytes."
        )

    if len(block) < 81:
        raise ValueError(
            "Block is too short."
        )

    header = block[:80]

    if len(header) != 80:
        raise ValueError(
            "Invalid block header size."
        )

    tx_count_prefix = block[80]

    if tx_count_prefix < 0xFD:

        transaction_count = (
            tx_count_prefix
        )

        offset = 81

    elif tx_count_prefix == 0xFD:

        if len(block) < 83:
            raise ValueError(
                "Incomplete CompactSize."
            )

        transaction_count = struct.unpack(
            "<H",
            block[81:83]
        )[0]

        offset = 83

    elif tx_count_prefix == 0xFE:

        if len(block) < 85:
            raise ValueError(
                "Incomplete CompactSize."
            )

        transaction_count = struct.unpack(
            "<I",
            block[81:85]
        )[0]

        offset = 85

    else:

        if len(block) < 89:
            raise ValueError(
                "Incomplete CompactSize."
            )

        transaction_count = struct.unpack(
            "<Q",
            block[81:89]
        )[0]

        offset = 89

    if transaction_count == 0:
        raise ValueError(
            "Block contains zero transactions."
        )

    return {
        "header": header,
        "transaction_count":
            transaction_count,
        "transactions_offset":
            offset,
        "block_size":
            len(block)
    }


# ============================================================
# TEST HEADER
# ============================================================

def create_test_header():
    """
    Create a deterministic 80-byte test header.

    This is only for testing block assembly.
    It is not necessarily a valid Proof-of-Work header.
    """

    version = struct.pack(
        "<I",
        0x20000000
    )

    previous_block_hash = (
        b"\x11" * 32
    )

    merkle_root = (
        b"\x22" * 32
    )

    timestamp = struct.pack(
        "<I",
        1231006505
    )

    bits = struct.pack(
        "<I",
        0x207FFFFF
    )

    nonce = struct.pack(
        "<I",
        0
    )

    header = (

        version

        + previous_block_hash

        + merkle_root

        + timestamp

        + bits

        + nonce

    )

    return header


# ============================================================
# TESTS
# ============================================================

def run_tests():

    print(
        "Bitcoin Block Builder Tests"
    )

    print(
        "=" * 50
    )

    # --------------------------------------------------------
    # Test 1: Header size
    # --------------------------------------------------------

    header = create_test_header()

    print(
        f"Header size: "
        f"{len(header)} bytes"
    )

    assert len(header) == 80

    print(
        "Header size: PASS"
    )

    # --------------------------------------------------------
    # Test 2: Coinbase-only block
    # --------------------------------------------------------

    coinbase_tx = (
        b"\x01"
        + b"\x02"
        + b"\x03"
    )

    block = build_block(

        header,

        coinbase_tx,

        []

    )

    print(
        f"Coinbase-only block size: "
        f"{len(block)} bytes"
    )

    structure = validate_block_structure(
        block
    )

    assert (
        structure[
            "transaction_count"
        ] == 1
    )

    print(
        "Coinbase-only block: PASS"
    )

    # --------------------------------------------------------
    # Test 3: Coinbase + transactions
    # --------------------------------------------------------

    tx1 = (
        b"\x11"
        + b"\x22"
    )

    tx2 = (
        b"\x33"
        + b"\x44"
        + b"\x55"
    )

    block = build_block(

        header,

        coinbase_tx,

        [
            tx1,
            tx2
        ]

    )

    structure = validate_block_structure(
        block
    )

    print(
        f"Transactions: "
        f"{structure['transaction_count']}"
    )

    assert (
        structure[
            "transaction_count"
        ] == 3
    )

    print(
        "Multiple transactions: PASS"
    )

    # --------------------------------------------------------
    # Test 4: Header preserved
    # --------------------------------------------------------

    assert (
        block[:80]
        == header
    )

    print(
        "Header preservation: PASS"
    )

    # --------------------------------------------------------
    # Test 5: Transaction count
    # --------------------------------------------------------

    assert (
        block[80]
        == 3
    )

    print(
        "Transaction count serialization: PASS"
    )

    print()
    print(
        "All block builder tests completed."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        run_tests()

    except AssertionError:

        print(
            "\nTEST FAILED"
        )

        raise

    except Exception as error:

        print(
            "\nERROR:"
        )

        print(
            str(error)
        )

        raise