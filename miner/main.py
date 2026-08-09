
#!/usr/bin/env python3

"""
Bitcoin Miner Lab
Working Developer Miner Logic Integrated into miner/main.py

REGTEST ONLY.

This main.py follows the known-working Windows developer miner:

1. Connect to Bitcoin Core
2. Verify regtest
3. Request getblocktemplate
4. Get mining address
5. Read live block height from template
6. Build BIP34 coinbase
7. Build SegWit witness commitment
8. Validate exact coinbase with Bitcoin Core
9. Calculate transaction Merkle root
10. Mine Regtest proof of work
11. Assemble complete block directly
12. Save raw block
13. Submit with submitblock
14. Verify chain height and accepted hash
"""

import os
import sys
import time
import struct
import hashlib


from .config import (
    EXPECTED_CHAIN,
    MINING_ADDRESS,
    MAX_TRANSACTIONS,
    OUTPUT_DIR,
)

from .rpc import BitcoinRPC


# ============================================================
# HASHING
# ============================================================

def sha256(data):

    return hashlib.sha256(
        data
    ).digest()


def double_sha256(data):

    return sha256(
        sha256(
            data
        )
    )


# ============================================================
# SERIALIZATION
# ============================================================

def encode_varint(n):

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

    return (
        b"\xff"
        + struct.pack(
            "<Q",
            n
        )
    )


def encode_script_number(n):

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


def push_data(data):

    length = len(
        data
    )


    if length < 0x4c:

        return (
            bytes([
                length
            ])
            + data
        )


    if length <= 0xff:

        return (
            b"\x4c"
            + bytes([
                length
            ])
            + data
        )


    if length <= 0xffff:

        return (
            b"\x4d"
            + struct.pack(
                "<H",
                length
            )
            + data
        )


    return (
        b"\x4e"
        + struct.pack(
            "<I",
            length
        )
        + data
    )


# ============================================================
# BIP34 COINBASE HEIGHT
# ============================================================

def build_coinbase_height_prefix(
    height
):

    height_data = (
        encode_script_number(
            height
        )
    )

    return push_data(
        height_data
    )


def validate_coinbase_height(
    script_sig,
    expected_height
):

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

    print(
        f"Coinbase height: "
        f"{expected_height}"
    )

    print(
        f"Expected height prefix: "
        f"{expected_prefix.hex()}"
    )

    print(
        f"Actual height prefix:   "
        f"{actual_prefix.hex()}"
    )


    if actual_prefix != expected_prefix:

        raise RuntimeError(

            "BIP34 coinbase height "
            "validation failed.\n"

            f"Expected: "
            f"{expected_prefix.hex()}\n"

            f"Actual: "
            f"{actual_prefix.hex()}"

        )


    print(
        "BIP34 height check: PASS"
    )


# ============================================================
# TEMPLATE TRANSACTIONS
# ============================================================

def get_template_transactions(
    template
):

    transactions = []


    for tx in template.get(
        "transactions",
        []
    ):

        raw = bytes.fromhex(
            tx["data"]
        )


        transactions.append({

            "raw":
                raw,

            "txid":
                tx["txid"],

            "wtxid":
                tx.get(
                    "hash",
                    tx["txid"]
                )

        })


    return transactions


# ============================================================
# MERKLE ROOT
# ============================================================

def merkle_root_from_hashes(
    hashes
):

    if not hashes:

        raise ValueError(
            "Hash list is empty."
        )


    current = [

        bytes.fromhex(
            h
        )[::-1]

        for h in hashes

    ]


    while len(
        current
    ) > 1:

        if len(
            current
        ) % 2:

            current.append(
                current[-1]
            )


        next_level = []


        for i in range(
            0,
            len(current),
            2
        ):

            next_level.append(

                double_sha256(

                    current[i]
                    + current[i + 1]

                )

            )


        current = (
            next_level
        )


    return current[0]


# ============================================================
# WITNESS COMMITMENT
# ============================================================

def calculate_witness_commitment(
    template_transactions
):

    # Coinbase WTXID is 32 zero bytes.

    witness_hashes = [

        "00" * 32

    ]


    for tx in template_transactions:

        witness_hashes.append(
            tx["wtxid"]
        )


    witness_merkle_root = (
        merkle_root_from_hashes(
            witness_hashes
        )
    )


    reserved_value = (
        b"\x00" * 32
    )


    commitment = double_sha256(

        witness_merkle_root
        + reserved_value

    )


    script = (

        b"\x6a"

        + b"\x24"

        + bytes.fromhex(
            "aa21a9ed"
        )

        + commitment

    )


    return script.hex()


# ============================================================
# COINBASE TRANSACTION
# ============================================================

def build_coinbase(
    template,
    mining_address,
    witness_commitment
):

    height = template[
        "height"
    ]

    coinbase_value = template[
        "coinbasevalue"
    ]


    # --------------------------------------------------------
    # BIP34 HEIGHT
    # --------------------------------------------------------

    height_data = (
        encode_script_number(
            height
        )
    )


    # --------------------------------------------------------
    # COINBASE EXTRA DATA
    # --------------------------------------------------------

    extra_data = (

        b"DeveloperMiner-Windows"

        + struct.pack(

            "<I",

            int(
                time.time()
            )
            & 0xffffffff

        )

    )


    script_sig = (

        push_data(
            height_data
        )

        + extra_data

    )


    if len(
        script_sig
    ) < 2:

        script_sig += (

            b"\x00"
            * (
                2
                - len(
                    script_sig
                )
            )

        )


    if len(
        script_sig
    ) > 100:

        raise RuntimeError(

            "Coinbase scriptSig "
            "exceeds 100 bytes."

        )


    validate_coinbase_height(

        script_sig,

        height

    )


    # --------------------------------------------------------
    # COINBASE INPUT
    # --------------------------------------------------------

    coinbase_input = (

        b"\x00" * 32

        + struct.pack(
            "<I",
            0xffffffff
        )

        + encode_varint(
            len(
                script_sig
            )
        )

        + script_sig

        + struct.pack(
            "<I",
            0xffffffff
        )

    )


    # --------------------------------------------------------
    # MINING ADDRESS SCRIPT
    # --------------------------------------------------------

    address_info = rpc.call(

        "getaddressinfo",

        [
            mining_address
        ]

    )


    script_pubkey_hex = (
        address_info.get(
            "scriptPubKey"
        )
    )


    if not script_pubkey_hex:

        raise RuntimeError(

            "Could not obtain "
            "scriptPubKey for "
            "mining address."

        )


    script_pubkey = bytes.fromhex(
        script_pubkey_hex
    )


    # --------------------------------------------------------
    # REWARD OUTPUT
    # --------------------------------------------------------

    reward_output = (

        struct.pack(
            "<Q",
            coinbase_value
        )

        + encode_varint(
            len(
                script_pubkey
            )
        )

        + script_pubkey

    )


    # --------------------------------------------------------
    # WITNESS COMMITMENT OUTPUT
    # --------------------------------------------------------

    commitment_script = bytes.fromhex(

        witness_commitment

    )


    commitment_output = (

        struct.pack(
            "<Q",
            0
        )

        + encode_varint(
            len(
                commitment_script
            )
        )

        + commitment_script

    )


    outputs = (

        reward_output
        + commitment_output

    )


    # --------------------------------------------------------
    # TRANSACTION SERIALIZATION
    # --------------------------------------------------------

    version = struct.pack(
        "<I",
        2
    )


    input_count = encode_varint(
        1
    )


    output_count = encode_varint(
        2
    )


    locktime = struct.pack(
        "<I",
        0
    )


    # Non-witness serialization
    # used for TXID.

    non_witness_tx = (

        version

        + input_count

        + coinbase_input

        + output_count

        + outputs

        + locktime

    )


    # --------------------------------------------------------
    # COINBASE WITNESS
    # --------------------------------------------------------

    witness_reserved_value = (
        b"\x00" * 32
    )


    witness = (

        encode_varint(
            1
        )

        + encode_varint(
            32
        )

        + witness_reserved_value

    )


    # --------------------------------------------------------
    # COMPLETE SEGWIT COINBASE
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
    # TXID
    # --------------------------------------------------------

    coinbase_txid_internal = (

        double_sha256(
            non_witness_tx
        )

    )


    coinbase_txid = (

        coinbase_txid_internal[
            ::-1
        ].hex()

    )


    return (
        segwit_tx,
        coinbase_txid
    )


# ============================================================
# CORE-SIDE COINBASE VALIDATION
# ============================================================

def validate_coinbase_with_core(
    coinbase_tx,
    expected_height,
    expected_coinbase_value
):

    print()
    print(
        "Validating serialized coinbase "
        "with Bitcoin Core..."
    )


    raw_hex = coinbase_tx.hex()


    decoded = rpc.call(

        "decoderawtransaction",

        [
            raw_hex
        ]

    )


    print(
        f"Decoded transaction version: "
        f"{decoded.get('version')}"
    )


    print(
        f"Decoded transaction inputs: "
        f"{len(decoded.get('vin', []))}"
    )


    print(
        f"Decoded transaction outputs: "
        f"{len(decoded.get('vout', []))}"
    )


    if len(
        decoded.get(
            "vin",
            []
        )
    ) != 1:

        raise RuntimeError(

            "Core validation failed: "
            "coinbase must have "
            "exactly one input."

        )


    vin = decoded[
        "vin"
    ][0]


    if "coinbase" not in vin:

        raise RuntimeError(

            "Core validation failed: "
            "input is not a "
            "coinbase input."

        )


    core_coinbase_hex = (
        vin["coinbase"]
    )


    expected_prefix = (

        build_coinbase_height_prefix(

            expected_height

        ).hex()

    )


    actual_prefix = (

        core_coinbase_hex[
            :len(expected_prefix)
        ]

    )


    print(
        "Core-decoded coinbase "
        f"scriptSig: {core_coinbase_hex}"
    )


    print(
        "Core-decoded height prefix: "
        f"{actual_prefix}"
    )


    if actual_prefix != expected_prefix:

        raise RuntimeError(

            "Core-side BIP34 "
            "validation failed.\n"

            f"Expected prefix: "
            f"{expected_prefix}\n"

            f"Core prefix: "
            f"{actual_prefix}"

        )


    if len(
        decoded["vout"]
    ) != 2:

        raise RuntimeError(

            "Core validation failed: "
            "expected exactly two "
            "coinbase outputs."

        )


    total_value = sum(

        int(
            round(
                output["value"]
                * 100000000
            )
        )

        for output
        in decoded["vout"]

    )


    if total_value != (
        expected_coinbase_value
    ):

        raise RuntimeError(

            "Core validation failed: "
            "coinbase output value "
            "does not match template."

        )


    print(
        "Bitcoin Core coinbase "
        "decode: PASS"
    )


# ============================================================
# COMPACT TARGET
# ============================================================

def compact_to_target(
    bits
):

    exponent = (
        bits >> 24
    )


    mantissa = (
        bits & 0x007fffff
    )


    if bits & 0x00800000:

        mantissa = -mantissa


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

        raise RuntimeError(

            f"Header is "
            f"{len(header)} bytes. "
            "Expected 80 bytes."

        )


    return header


# ============================================================
# PROOF OF WORK
# ============================================================

def mine_header(
    version,
    previous_block_hash,
    merkle_root,
    curtime,
    bits
):

    target = compact_to_target(
        bits
    )


    if target <= 0:

        raise RuntimeError(
            "Invalid proof-of-work target."
        )


    print()
    print(
        "Starting Proof of Work..."
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


        hash_internal = (
            double_sha256(
                header
            )
        )


        block_hash = (
            hash_internal[
                ::-1
            ].hex()
        )


        hash_int = int.from_bytes(

            hash_internal,

            byteorder="little"

        )


        hashes_done += 1


        if hash_int <= target:

            elapsed = (
                time.time()
                - start_time
            )


            print()
            print(
                "*** VALID PROOF "
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
            nonce
            % 1_000_000
            == 0
        ):

            print(

                f"\rNonce: "
                f"{nonce:,}",

                end="",

                flush=True

            )


    raise RuntimeError(
        "Nonce space exhausted."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    global rpc

    print(
        "=" * 60
    )

    print(
        "BITCOIN MINER LAB"
    )

    print(
        "WORKING DEVELOPER MINER PIPELINE"
    )

    print(
        "Windows SegWit + BIP34"
    )

    print(
        "Bitcoin Core Regtest"
    )

    print(
        "=" * 60
    )


    # --------------------------------------------------------
    # RPC
    # --------------------------------------------------------

    print()
    print(
        "Connecting to Bitcoin Core..."
    )


    rpc = BitcoinRPC()


    info = rpc.call(
        "getblockchaininfo"
    )


    print()
    print(
        "Connected to Bitcoin Core."
    )


    print(
        f"Chain: "
        f"{info['chain']}"
    )


    print(
        f"Height: "
        f"{info['blocks']}"
    )


    if info["chain"] != EXPECTED_CHAIN:

        raise RuntimeError(

            "SAFETY STOP: "
            "This miner only runs "
            "on regtest."

        )


    print(
        "Regtest safety check: PASS"
    )


    # --------------------------------------------------------
    # MINING ADDRESS
    # --------------------------------------------------------

    mining_address = (
        MINING_ADDRESS
    )


    if not mining_address:

        mining_address = rpc.call(

            "getnewaddress",

            [
                "developer-miner",
                "bech32"
            ]

        )


    print()
    print(
        f"Mining address: "
        f"{mining_address}"
    )


    # --------------------------------------------------------
    # BLOCK TEMPLATE
    # --------------------------------------------------------

    print()
    print(
        "Requesting block template..."
    )


    template = rpc.call(

        "getblocktemplate",

        [
            {
                "rules": [
                    "segwit"
                ]
            }
        ]

    )


    print()
    print(
        "Block Template"
    )

    print(
        "-" * 60
    )


    print(
        f"Height: "
        f"{template['height']}"
    )


    print(
        f"Previous block: "
        f"{template['previousblockhash']}"
    )


    print(
        f"Version: "
        f"{template['version']}"
    )


    print(
        f"Bits: "
        f"{template['bits']}"
    )


    print(
        f"Curtime: "
        f"{template['curtime']}"
    )


    print(
        f"Coinbase value: "
        f"{template['coinbasevalue']}"
    )


    # --------------------------------------------------------
    # TEMPLATE TRANSACTIONS
    # --------------------------------------------------------

    template_txs = (
        get_template_transactions(
            template
        )
    )


    if MAX_TRANSACTIONS > 0:

        template_txs = (

            template_txs[
                :MAX_TRANSACTIONS
            ]

        )


    print(
        f"Template transactions: "
        f"{len(template_txs)}"
    )


    # --------------------------------------------------------
    # WITNESS COMMITMENT
    # --------------------------------------------------------

    witness_commitment = (

        calculate_witness_commitment(

            template_txs

        )

    )


    print(
        f"Witness commitment: "
        f"{witness_commitment}"
    )


    # --------------------------------------------------------
    # COINBASE
    # --------------------------------------------------------

    print()
    print(
        "Building coinbase..."
    )


    (
        coinbase_tx,
        coinbase_txid
    ) = build_coinbase(

        template,

        mining_address,

        witness_commitment

    )


    print(
        f"Coinbase TXID: "
        f"{coinbase_txid}"
    )


    # --------------------------------------------------------
    # CORE COINBASE VALIDATION
    # --------------------------------------------------------

    validate_coinbase_with_core(

        coinbase_tx,

        template["height"],

        template["coinbasevalue"]

    )


    # --------------------------------------------------------
    # MERKLE ROOT
    # --------------------------------------------------------

    txids = [
        coinbase_txid
    ]


    for tx in template_txs:

        txids.append(
            tx["txid"]
        )


    merkle_root = (

        merkle_root_from_hashes(

            txids

        )

    )


    print()
    print(
        f"Transaction Merkle root: "
        f"{merkle_root[::-1].hex()}"
    )


    print(
        f"Transactions in block: "
        f"{len(txids)}"
    )


    # --------------------------------------------------------
    # PROOF OF WORK
    # --------------------------------------------------------

    (
        header,
        block_hash
    ) = mine_header(

        version=template[
            "version"
        ],

        previous_block_hash=template[
            "previousblockhash"
        ],

        merkle_root=merkle_root,

        curtime=template[
            "curtime"
        ],

        bits=int(
            template["bits"],
            16
        )

    )


    print()
    print(
        f"Header: "
        f"{header.hex()}"
    )


    # --------------------------------------------------------
    # COMPLETE BLOCK
    #
    # IMPORTANT:
    # Assemble directly from the known-working
    # developer miner implementation.
    # --------------------------------------------------------

    full_block = (

        header

        + encode_varint(
            len(txids)
        )

        + coinbase_tx

    )


    for tx in template_txs:

        full_block += tx["raw"]


    raw_block_hex = (
        full_block.hex()
    )


    print()
    print(
        f"Full block size: "
        f"{len(full_block):,} bytes"
    )


    # --------------------------------------------------------
    # SAVE BLOCK
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


    filename = os.path.join(

        OUTPUT_DIR,

        f"{block_hash}.hex"

    )


    with open(

        filename,

        "w",

        encoding="utf-8"

    ) as f:

        f.write(
            raw_block_hex
        )


    print(
        "Raw block saved to:"
    )

    print(
        filename
    )


    # --------------------------------------------------------
    # SUBMIT
    # --------------------------------------------------------

    print()
    print(
        "Submitting block..."
    )


    result = rpc.call(

        "submitblock",

        [
            raw_block_hex
        ]

    )


    if result is not None:

        print()
        print(
            "BLOCK REJECTED"
        )

        print(
            f"Reason: "
            f"{result}"
        )

        return


    # --------------------------------------------------------
    # ACCEPTED
    # --------------------------------------------------------

    print()
    print(
        "SUCCESS!"
    )


    print(
        "Bitcoin Core accepted "
        "the block."
    )


    # --------------------------------------------------------
    # VERIFY
    # --------------------------------------------------------

    new_height = rpc.call(
        "getblockcount"
    )


    accepted_hash = rpc.call(

        "getblockhash",

        [
            new_height
        ]

    )


    print()
    print(
        f"New blockchain height: "
        f"{new_height}"
    )


    print(
        "Accepted block hash:"
    )


    print(
        accepted_hash
    )


    print()
    print(
        "Developer mining "
        "cycle complete."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\n\nMining stopped."
        )

        sys.exit(1)

    except Exception as error:

        print()
        print(
            "ERROR:"
        )

        print(
            str(error)
        )

        raise

