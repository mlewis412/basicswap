#!/usr/bin/env python3
"""Read-only preflight for reusing BasicSwap's current DOGE RPC adapter.

This is not an integration or a swap-safety test. It only queries node identity
and RPC help. No wallet creation, key import, signing, or broadcasting occurs.
"""

import argparse
import json
import re
import subprocess
import sys


GENESIS = {
    "mainnet": "37981c0c48b8d48965376c8a42ece9a0838daadb93ff975cb091f57f8c2a5faa",
    "testnet": "f9f4ea4ae7f6ea4c55040ede2019ba0a53e262f46ec9bce3dcda2cb11f96fc52",
    "regtest": "770975b0f98319520694563de107ff94fd501c0d1c16f3a405868faf36b51c28",
}

# These methods are used by the inherited BTC interface. An adapter can replace
# individual methods; absence here does not mean PEP cannot support atomic swaps.
RPC_METHODS = (
    "listwallets",
    "createwallet",
    "sethdseed",
    "getwalletinfo",
    "getnewaddress",
    "getaddressinfo",
    "fundrawtransaction",
    "signrawtransactionwithwallet",
    "getbalances",
    "importaddress",
    "rescanblockchain",
    "gettransaction",
    "gettxout",
    "listunspent",
)


def assess(genesis, help_text, network):
    # Match full method names, not examples, substring matches, or error text.
    advertised = set(re.findall(r"^([a-z][a-z0-9_]*)\b", help_text, re.MULTILINE))
    identity_matches = genesis.strip().strip('"') == GENESIS[network]
    missing = [method for method in RPC_METHODS if method not in advertised]
    return {
        "network": network,
        "pepecoin_genesis_matches": identity_matches,
        "missing_doge_adapter_rpc_methods": missing,
        "direct_doge_adapter_rpc_preflight": (
            "pass" if identity_matches and not missing else "blocked"
        ),
        "swap_safety_validated": False,
        "note": "RPC availability alone does not validate semantics, recovery, or swaps.",
    }


def inspect_node(cli, network, datadir=None, timeout=15):
    command = [cli]
    if network != "mainnet":
        command.append("-" + network)
    if datadir:
        command.append("-datadir=" + datadir)

    def query(*args):
        result = subprocess.run(
            command + list(args),
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout

    return assess(query("getblockhash", "0"), query("help"), network)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", default="pepecoin-cli")
    parser.add_argument("--network", choices=tuple(GENESIS), default="regtest")
    parser.add_argument("--datadir")
    args = parser.parse_args()
    try:
        result = inspect_node(args.cli, args.network, args.datadir)
    except (OSError, subprocess.SubprocessError):
        # Do not echo command arguments, node config paths, or daemon stderr.
        print("Node query failed. Check the CLI, node, and local configuration.", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["direct_doge_adapter_rpc_preflight"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
