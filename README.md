# Bitcoin Miner Lab

A modular Bitcoin mining and block-construction laboratory built in Python for **Bitcoin Core regtest**.

This project demonstrates how a Bitcoin miner can obtain a block template, construct a valid coinbase transaction, calculate the Merkle root, perform Proof of Work, assemble the complete block, and submit it to Bitcoin Core.

> **REGTEST ONLY**

## What This Project Does

The miner implements a complete developer-oriented block-building pipeline:

1. Connects to Bitcoin Core through JSON-RPC
2. Verifies that Bitcoin Core is running on `regtest`
3. Requests a block template with `getblocktemplate`
4. Reads the current block height and previous block hash
5. Builds a BIP34-compatible coinbase transaction
6. Includes the current block height in the coinbase `scriptSig`
7. Builds the SegWit witness commitment
8. Calculates the transaction Merkle root
9. Constructs the Bitcoin block header
10. Performs Proof of Work
11. Serializes the complete block
12. Saves the raw block to disk
13. Submits the block with `submitblock`
14. Verifies that Bitcoin Core accepted the block

The miner can also include transactions supplied by the Bitcoin Core block template.

## Project Structure

```text
Bitcoin-miner-lab/
│
├── miner/
│   ├── __init__.py
│   ├── main.py
│   ├── block_builder.py
│   ├── coinbase.py
│   ├── config.py
│   ├── merkle.py
│   ├── pow.py
│   ├── rpc.py
│   ├── serialization.py
│   ├── submit.py
│   └── witness.py
│
├── .gitignore
└── README.md
```

## Mining Pipeline

```text
Bitcoin Core
     │
     ▼
getblocktemplate
     │
     ▼
Block Template
     │
     ├── Block height
     ├── Previous block hash
     ├── Version
     ├── Bits / target
     ├── Timestamp
     └── Transactions
     │
     ▼
Coinbase Transaction
     │
     ▼
Witness Commitment
     │
     ▼
Transaction Merkle Root
     │
     ▼
Block Header
     │
     ▼
Proof of Work
     │
     ▼
Complete Serialized Block
     │
     ▼
submitblock
     │
     ▼
Bitcoin Core
     │
     ▼
Accepted Regtest Block
```

## Requirements

* Windows
* Python 3
* Bitcoin Core
* Bitcoin Core running in `regtest`
* JSON-RPC enabled
* A Bitcoin Core wallet/address for the mining reward

## Running Bitcoin Core

Start Bitcoin Core in regtest mode and make sure RPC access is available.

The miner performs a safety check before mining:

```text
Chain: regtest
Regtest safety check: PASS
```

The project is intentionally designed for regtest development and experimentation.

## Run the Miner

From the project directory:

```bat
cd C:\Bitcoin-miner-lab
python -m miner.main
```

A successful cycle looks like:

```text
Requesting block template...

## Block Template

Height: 124
Previous block: ...
Version: 536870912
Bits: 207fffff
Coinbase value: 5000001066
Template transactions: 8

Building coinbase...
BIP34 height check: PASS

Starting Proof of Work...

*** VALID PROOF OF WORK FOUND ***

Submitting block...

SUCCESS!
Bitcoin Core accepted the block.

New blockchain height: 124
```

## Coinbase Validation

The project verifies that the coinbase contains the correct current block height.

For example:

```text
Coinbase height: 124
Expected height prefix: 017c
Actual height prefix:   017c
BIP34 height check: PASS
```

The serialized coinbase is also decoded through Bitcoin Core to verify that the transaction is interpreted correctly.

## Transaction Mining

When Bitcoin Core provides transactions through `getblocktemplate`, the miner can include those transactions in the constructed block.

The resulting block therefore contains:

* Coinbase transaction
* Mempool transactions
* Merkle root covering all transactions
* SegWit witness commitment
* Valid Proof of Work

## Output

Successfully mined blocks are saved locally under:

```text
mined_blocks/
```

The saved block contains the raw serialized Bitcoin block that was submitted to Bitcoin Core.

## Important

This project is a **Bitcoin Core regtest development laboratory**.

Regtest coins and blocks are not Bitcoin mainnet coins.

The purpose of this project is to understand and experiment with Bitcoin's block-construction and mining pipeline without risking real Bitcoin.

## Learning Goals

This project is intended to provide practical experience with:

* Bitcoin block structure
* Bitcoin block headers
* BIP34 coinbase height
* Coinbase transactions
* SegWit witness commitments
* Transaction serialization
* Transaction IDs
* Merkle trees
* Proof of Work
* Compact difficulty representation (`nBits`)
* Bitcoin Core JSON-RPC
* `getblocktemplate`
* `submitblock`
* Mempool transaction selection
* Regtest mining

## Status

**Working**

The modular miner has successfully:

* Connected to Bitcoin Core regtest
* Retrieved block templates
* Built valid coinbase transactions
* Passed BIP34 height validation
* Built witness commitments
* Calculated transaction Merkle roots
* Performed Proof of Work
* Serialized complete blocks
* Included template transactions
* Submitted blocks to Bitcoin Core
* Received successful block acceptance from Bitcoin Core

## License

This project is provided for educational and development purposes.
