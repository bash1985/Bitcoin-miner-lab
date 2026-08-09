#!/usr/bin/env python3

"""
Bitcoin Miner Lab - Windows Configuration

Central configuration for Bitcoin Core Regtest RPC.
"""

import os


# ============================================================
# BITCOIN CORE RPC CONFIGURATION
# ============================================================

RPC_HOST = "127.0.0.1"
RPC_PORT = 18443


# ============================================================
# BITCOIN CORE CONFIGURATION FILE
# ============================================================

BITCOIN_CONF = os.path.join(
    os.environ.get("APPDATA", ""),
    "Bitcoin",
    "bitcoin.conf"
)


# ============================================================
# MINING CONFIGURATION
# ============================================================

MINING_ADDRESS = ""

MAX_TRANSACTIONS = 0

OUTPUT_DIR = "mined_blocks"


# ============================================================
# NETWORK
# ============================================================

EXPECTED_CHAIN = "regtest"


# ============================================================
# DISPLAY CONFIGURATION
# ============================================================

PROJECT_NAME = "Bitcoin Miner Lab"
MINER_NAME = "Developer Miner Windows"


def show_config():

    print("=" * 60)
    print(PROJECT_NAME)
    print("=" * 60)

    print(f"RPC Host: {RPC_HOST}")
    print(f"RPC Port: {RPC_PORT}")
    print(f"Bitcoin Core Config: {BITCOIN_CONF}")
    print(f"Expected Chain: {EXPECTED_CHAIN}")
    print(f"Mining Address: {MINING_ADDRESS or 'Automatic'}")
    print(f"Max Transactions: {MAX_TRANSACTIONS}")
    print(f"Output Directory: {OUTPUT_DIR}")


if __name__ == "__main__":

    show_config()