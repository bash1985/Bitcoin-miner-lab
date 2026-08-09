#!/usr/bin/env python3

"""
Bitcoin Miner Lab - Bitcoin Core RPC Client

Windows Regtest RPC connection module.
"""

import json
import base64
import urllib.request
import urllib.error

from .config import (
    RPC_HOST,
    RPC_PORT,
    BITCOIN_CONF,
)


# ============================================================
# READ BITCOIN.CONF
# ============================================================

def read_config_file(path):

    config = {}

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            for line in f:

                line = line.strip()

                if not line:
                    continue

                if line.startswith("#"):
                    continue

                if line.startswith(";"):
                    continue

                if "=" not in line:
                    continue

                key, value = line.split(
                    "=",
                    1
                )

                config[
                    key.strip()
                ] = value.strip()

    except FileNotFoundError:

        pass

    return config


# ============================================================
# LOAD RPC CREDENTIALS
# ============================================================

def load_rpc_credentials():

    rpc_user = None
    rpc_password = None

    # First check environment variables.

    rpc_user = (
        __import__("os")
        .environ
        .get("BTC_RPC_USER")
    )

    rpc_password = (
        __import__("os")
        .environ
        .get("BTC_RPC_PASSWORD")
    )

    if rpc_user and rpc_password:

        print(
            "RPC credentials loaded "
            "from environment variables."
        )

        return (
            rpc_user,
            rpc_password
        )

    # Otherwise read bitcoin.conf.

    config = read_config_file(
        BITCOIN_CONF
    )

    rpc_user = config.get(
        "rpcuser"
    )

    rpc_password = config.get(
        "rpcpassword"
    )

    if not rpc_user or not rpc_password:

        raise RuntimeError(

            "RPC credentials not found.\n\n"

            f"Expected configuration file:\n"
            f"{BITCOIN_CONF}\n\n"

            "Make sure bitcoin.conf contains:\n"
            "rpcuser=YOUR_USERNAME\n"
            "rpcpassword=YOUR_PASSWORD"

        )

    print(
        "RPC credentials loaded "
        "automatically from bitcoin.conf."
    )

    return (
        rpc_user,
        rpc_password
    )


# ============================================================
# RPC CLIENT
# ============================================================

class BitcoinRPC:

    def __init__(self):

        (
            self.rpc_user,
            self.rpc_password
        ) = load_rpc_credentials()

        self.url = (

            f"http://"
            f"{RPC_HOST}:"
            f"{RPC_PORT}/"

        )


    def call(
        self,
        method,
        params=None
    ):

        if params is None:

            params = []


        payload = json.dumps({

            "jsonrpc": "1.0",

            "id": "bitcoin-miner-lab",

            "method": method,

            "params": params

        }).encode(
            "utf-8"
        )


        credentials = (

            f"{self.rpc_user}:"
            f"{self.rpc_password}"

        ).encode(
            "utf-8"
        )


        auth = base64.b64encode(

            credentials

        ).decode(
            "ascii"
        )


        request = urllib.request.Request(

            self.url,

            data=payload,

            headers={

                "Content-Type":
                    "application/json",

                "Authorization":
                    f"Basic {auth}"

            }

        )


        try:

            with urllib.request.urlopen(

                request,

                timeout=30

            ) as response:

                result = json.loads(

                    response
                    .read()
                    .decode(
                        "utf-8"
                    )

                )


        except urllib.error.HTTPError as e:

            raise RuntimeError(

                f"RPC HTTP error: "
                f"{e.code}\n"
                f"{e.read().decode('utf-8', errors='replace')}"

            )


        except urllib.error.URLError as e:

            raise RuntimeError(

                "Could not connect to "
                "Bitcoin Core RPC.\n"
                "Make sure Bitcoin Core "
                "Regtest is running.\n\n"
                f"Details: {e}"

            )


        if result.get(
            "error"
        ) is not None:

            raise RuntimeError(

                "Bitcoin Core RPC error:\n"

                + json.dumps(

                    result["error"],

                    indent=2

                )

            )


        return result[
            "result"
        ]


# ============================================================
# TEST
# ============================================================

def main():

    print(
        "=" * 60
    )

    print(
        "Bitcoin Miner Lab RPC Test"
    )

    print(
        "=" * 60
    )


    rpc = BitcoinRPC()


    blockchain = rpc.call(

        "getblockchaininfo"

    )


    print(
        "\nConnected to Bitcoin Core."
    )

    print(
        f"Chain: "
        f"{blockchain['chain']}"
    )

    print(
        f"Blocks: "
        f"{blockchain['blocks']}"
    )

    print(
        f"Headers: "
        f"{blockchain['headers']}"
    )


    if blockchain[
        "chain"
    ] != "regtest":

        raise RuntimeError(

            "Safety stop: "
            "Bitcoin Core is not "
            "running on regtest."

        )


    print(
        "\nRPC connection test: PASS"
    )


if __name__ == "__main__":

    main()