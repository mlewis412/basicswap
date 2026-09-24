"""Dependency-free tests; no daemon and no funded wallet required."""

import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "pep_preflight",
    Path(__file__).resolve().parents[1] / "scripts/check_pepecoin_compatibility.py",
)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class TestPepecoinPreflight(unittest.TestCase):
    def test_stock_legacy_api_does_not_pass_as_modern_api(self):
        result = preflight.assess(
            preflight.GENESIS["mainnet"],
            "signrawtransaction hex\nvalidateaddress address\ngetwalletinfo\n",
            "mainnet",
        )
        self.assertEqual(result["direct_doge_adapter_rpc_preflight"], "blocked")
        self.assertIn("sethdseed", result["missing_doge_adapter_rpc_methods"])
        self.assertIn("signrawtransactionwithwallet", result["missing_doge_adapter_rpc_methods"])

    def test_wrong_chain_is_blocked_even_with_all_methods(self):
        result = preflight.assess("0" * 64, "\n".join(preflight.RPC_METHODS), "regtest")
        self.assertFalse(result["pepecoin_genesis_matches"])
        self.assertEqual(result["direct_doge_adapter_rpc_preflight"], "blocked")

    def test_each_network_pass_still_does_not_claim_swap_safety(self):
        for network, genesis in preflight.GENESIS.items():
            with self.subTest(network=network):
                result = preflight.assess(genesis + "\n", "\n".join(preflight.RPC_METHODS), network)
                self.assertEqual(result["direct_doge_adapter_rpc_preflight"], "pass")
                self.assertFalse(result["swap_safety_validated"])

    def test_method_substrings_do_not_pass(self):
        result = preflight.assess(
            preflight.GENESIS["regtest"],
            "getaddressinfo_fake\n  example sethdseed\n", "regtest",
        )
        self.assertIn("getaddressinfo", result["missing_doge_adapter_rpc_methods"])
        self.assertIn("sethdseed", result["missing_doge_adapter_rpc_methods"])

    @patch.object(preflight.subprocess, "run")
    def test_only_read_only_commands_are_executed_without_shell(self, run):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, preflight.GENESIS["regtest"]),
            subprocess.CompletedProcess([], 0, "\n".join(preflight.RPC_METHODS)),
        ]
        preflight.inspect_node("pepecoin-cli", "regtest", "/tmp/test wallet")
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands, [
            ["pepecoin-cli", "-regtest", "-datadir=/tmp/test wallet", "getblockhash", "0"],
            ["pepecoin-cli", "-regtest", "-datadir=/tmp/test wallet", "help"],
        ])
        for call in run.call_args_list:
            self.assertNotIn("shell", call.kwargs)
            self.assertEqual(call.kwargs["timeout"], 15)


if __name__ == "__main__":
    unittest.main()
