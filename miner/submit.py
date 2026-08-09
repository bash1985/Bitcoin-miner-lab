#!/usr/bin/env python3

"""
Bitcoin Miner Lab - Block Submission

This module handles:

1. Submitting a serialized raw block to Bitcoin Core.
2. Detecting block acceptance or rejection.
3. Reading the current blockchain height.
4. Retrieving a block hash.
5. Verifying the current chain tip.

Uses the BitcoinRPC class from miner.rpc.

Regtest-focused educational implementation.
"""

from .rpc import BitcoinRPC


# ============================================================
# RPC CLIENT
# ============================================================

rpc = BitcoinRPC()


# ============================================================
# SUBMIT BLOCK
# ============================================================

def submit_block(raw_block_hex):
    """
    Submit a raw serialized block to Bitcoin Core.

    Parameters
    ----------
    raw_block_hex : str
        Complete serialized block in hexadecimal form.

    Returns
    -------
    str or None
        None means Bitcoin Core accepted the block.
        A string means Bitcoin Core rejected the block.
    """

    if not isinstance(
        raw_block_hex,
        str
    ):
        raise TypeError(
            "raw_block_hex must be a string."
        )

    if not raw_block_hex:
        raise ValueError(
            "Raw block hex cannot be empty."
        )

    try:

        bytes.fromhex(
            raw_block_hex
        )

    except ValueError as error:

        raise ValueError(
            "raw_block_hex contains "
            "invalid hexadecimal data."
        ) from error

    return rpc.call(
        "submitblock",
        [
            raw_block_hex
        ]
    )


# ============================================================
# CHECK SUBMISSION RESULT
# ============================================================

def check_submission_result(
    result
):
    """
    Check the result returned by submitblock.

    Bitcoin Core submitblock returns:

        None
            Block accepted.

        String
            Block rejected.
    """

    return result is None


# ============================================================
# GET BLOCKCHAIN HEIGHT
# ============================================================

def get_chain_height():
    """
    Return the current Bitcoin Core blockchain height.
    """

    return rpc.call(
        "getblockcount"
    )


# ============================================================
# GET BLOCK HASH
# ============================================================

def get_block_hash(
    height
):
    """
    Return the block hash at a given height.
    """

    if not isinstance(
        height,
        int
    ):
        raise TypeError(
            "Block height must be an integer."
        )

    if height < 0:
        raise ValueError(
            "Block height cannot be negative."
        )

    return rpc.call(
        "getblockhash",
        [
            height
        ]
    )


# ============================================================
# VERIFY CHAIN TIP
# ============================================================

def verify_chain_tip(
    expected_height=None,
    expected_block_hash=None
):
    """
    Verify the current Bitcoin Core chain tip.

    Parameters
    ----------
    expected_height : int, optional
        Expected blockchain height.

    expected_block_hash : str, optional
        Expected block hash.

    Returns
    -------
    dict
        Verification result.
    """

    current_height = (
        get_chain_height()
    )

    current_hash = (
        get_block_hash(
            current_height
        )
    )

    # --------------------------------------------------------
    # Check expected height
    # --------------------------------------------------------

    if (
        expected_height is not None
        and current_height
        != expected_height
    ):

        return {

            "verified": False,

            "height":
                current_height,

            "block_hash":
                current_hash,

            "reason":
                "Blockchain height does not "
                "match expected height."

        }

    # --------------------------------------------------------
    # Check expected block hash
    # --------------------------------------------------------

    if (
        expected_block_hash is not None
        and current_hash
        != expected_block_hash
    ):

        return {

            "verified": False,

            "height":
                current_height,

            "block_hash":
                current_hash,

            "reason":
                "Block hash does not "
                "match expected hash."

        }

    return {

        "verified": True,

        "height":
            current_height,

        "block_hash":
            current_hash,

        "reason":
            "Chain tip verified."

    }


# ============================================================
# SUBMIT AND VERIFY
# ============================================================

def submit_and_verify(
    raw_block_hex,
    expected_block_hash=None
):
    """
    Submit a block and verify Bitcoin Core acceptance.

    Returns
    -------
    dict
        Complete submission and verification result.
    """

    print(
        "\nSubmitting block..."
    )

    result = submit_block(
        raw_block_hex
    )

    # --------------------------------------------------------
    # Block rejected
    # --------------------------------------------------------

    if not check_submission_result(
        result
    ):

        print(
            "\nBLOCK REJECTED"
        )

        print(
            f"Reason: {result}"
        )

        return {

            "accepted": False,

            "verified": False,

            "reason":
                result

        }

    # --------------------------------------------------------
    # Block accepted
    # --------------------------------------------------------

    print(
        "\nBLOCK ACCEPTED"
    )

    print(
        "Bitcoin Core accepted "
        "the submitted block."
    )

    # --------------------------------------------------------
    # Verify chain tip
    # --------------------------------------------------------

    verification = (
        verify_chain_tip(
            expected_block_hash=
                expected_block_hash
        )
    )

    if verification[
        "verified"
    ]:

        print(
            "\nBLOCK VERIFICATION: PASS"
        )

        print(
            f"New blockchain height: "
            f"{verification['height']}"
        )

        print(
            f"Accepted block hash:\n"
            f"{verification['block_hash']}"
        )

    else:

        print(
            "\nBLOCK VERIFICATION: FAILED"
        )

        print(
            verification[
                "reason"
            ]
        )

    return {

        "accepted": True,

        **verification

    }


# ============================================================
# TESTS
# ============================================================

def run_tests():

    print(
        "Bitcoin Block Submission Tests"
    )

    print(
        "=" * 50
    )

    # --------------------------------------------------------
    # Test 1: RPC connection
    # --------------------------------------------------------

    height = (
        get_chain_height()
    )

    print(
        f"Current blockchain height: "
        f"{height}"
    )

    assert isinstance(
        height,
        int
    )

    assert height >= 0

    print(
        "Blockchain height RPC: PASS"
    )

    # --------------------------------------------------------
    # Test 2: Get block hash
    # --------------------------------------------------------

    block_hash = (
        get_block_hash(
            height
        )
    )

    print(
        f"Current tip hash:\n"
        f"{block_hash}"
    )

    assert isinstance(
        block_hash,
        str
    )

    assert len(
        block_hash
    ) == 64

    print(
        "Block hash RPC: PASS"
    )

    # --------------------------------------------------------
    # Test 3: Submission result handling
    # --------------------------------------------------------

    assert (
        check_submission_result(
            None
        )
        is True
    )

    assert (
        check_submission_result(
            "bad-cb-height"
        )
        is False
    )

    print(
        "Submission result handling: PASS"
    )

    # --------------------------------------------------------
    # Test 4: Chain tip verification
    # --------------------------------------------------------

    verification = (
        verify_chain_tip(

            expected_height=
                height,

            expected_block_hash=
                block_hash

        )
    )

    assert (
        verification[
            "verified"
        ]
        is True
    )

    print(
        "Chain tip verification: PASS"
    )

    print()

    print(
        "All block submission tests completed."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        run_tests()

    except KeyboardInterrupt:

        print(
            "\n\nTests stopped."
        )

    except Exception as error:

        print(
            "\nERROR:"
        )

        print(
            str(error)
        )

        raise