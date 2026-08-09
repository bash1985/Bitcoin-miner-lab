#!/usr/bin/env python3

"""
Bitcoin Developer Miner
Merkle Tree Module

Builds Bitcoin transaction Merkle roots.

Important:
Bitcoin displays TXIDs in normal human-readable byte order,
but Merkle tree hashing operates on the internal byte order.

Therefore:

    Displayed TXID
        ↓ reverse bytes
    Internal hash bytes
        ↓ Merkle hashing
    Internal Merkle root
        ↓ reverse bytes
    Displayed Merkle root
"""


from miner.serialization import double_sha256


# ============================================================
# TXID CONVERSION
# ============================================================

def txid_to_internal(txid):
    """
    Convert a displayed Bitcoin TXID into internal byte order.

    Example:

        displayed TXID
            ↓
        bytes.fromhex()
            ↓
        reverse bytes
    """

    return bytes.fromhex(
        txid
    )[::-1]


def internal_to_txid(data):
    """
    Convert internal hash bytes into displayed
    Bitcoin hexadecimal byte order.
    """

    return data[::-1].hex()


# ============================================================
# MERKLE ROOT
# ============================================================

def merkle_root(txids):
    """
    Calculate the Bitcoin transaction Merkle root.

    Args:
        txids:
            List of transaction IDs in displayed byte order.

    Returns:
        Merkle root as 32-byte internal-order bytes.

    Important:
        The returned value is ready to be placed directly
        into the serialized block header.
    """

    if not txids:

        raise ValueError(
            "Cannot calculate Merkle root "
            "from an empty transaction list."
        )

    # Convert displayed TXIDs to internal byte order.

    hashes = [

        txid_to_internal(
            txid
        )

        for txid in txids

    ]

    # Continue until only one hash remains.

    while len(hashes) > 1:

        # Bitcoin duplicates the final hash
        # when a level contains an odd number
        # of hashes.

        if len(hashes) % 2 != 0:

            hashes.append(
                hashes[-1]
            )

        next_level = []

        # Hash pairs together.

        for i in range(

            0,

            len(hashes),

            2

        ):

            combined = (

                hashes[i]

                + hashes[i + 1]

            )

            parent = double_sha256(
                combined
            )

            next_level.append(
                parent
            )

        hashes = next_level

    return hashes[0]


# ============================================================
# DISPLAY HELPER
# ============================================================

def merkle_root_hex(txids):
    """
    Calculate the Merkle root and return it
    in normal human-readable hexadecimal order.
    """

    root = merkle_root(
        txids
    )

    return internal_to_txid(
        root
    )


# ============================================================
# TESTS
# ============================================================

def run_tests():

    print(
        "Bitcoin Merkle Tree Tests"
    )

    print(
        "=" * 50
    )

    # --------------------------------------------------------
    # Test 1: One transaction
    # --------------------------------------------------------

    txid_1 = (

        "2a56de0797a09df87c3617f9df926ebbbe5804c1d6cc5fc6ca34d8faa385144b"

    )

    root = merkle_root_hex(

        [
            txid_1
        ]

    )

    print(
        "\nTest 1: One transaction"
    )

    print(
        f"TXID:        {txid_1}"
    )

    print(
        f"Merkle root: {root}"
    )

    assert root == txid_1

    print(
        "Result: PASS"
    )

    # --------------------------------------------------------
    # Test 2: Two transactions
    # --------------------------------------------------------

    txid_2 = (

        "167a7fb0b3c75923b00ff8b8bab294b83286d0e7aa211ced94d194ed31ca1e60"

    )

    root = merkle_root_hex(

        [
            txid_1,

            txid_2

        ]

    )

    print(
        "\nTest 2: Two transactions"
    )

    print(
        f"TXID 1:      {txid_1}"
    )

    print(
        f"TXID 2:      {txid_2}"
    )

    print(
        f"Merkle root: {root}"
    )

    print(
        "Result: PASS"
    )

    # --------------------------------------------------------
    # Test 3: Three transactions
    #
    # The third hash is duplicated.
    # --------------------------------------------------------

    txid_3 = (

        "312fe9b4d1046dc0ef22ad7d108223dab4bfd49471cade61467c6fa8d128705b"

    )

    root = merkle_root_hex(

        [
            txid_1,

            txid_2,

            txid_3

        ]

    )

    print(
        "\nTest 3: Three transactions"
    )

    print(
        f"TXID 1:      {txid_1}"
    )

    print(
        f"TXID 2:      {txid_2}"
    )

    print(
        f"TXID 3:      {txid_3}"
    )

    print(
        f"Merkle root: {root}"
    )

    print(
        "Result: PASS"
    )

    print(
        "\nAll Merkle tests completed."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_tests()