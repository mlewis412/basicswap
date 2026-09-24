# Pepecoin (PEP) integration proposal and preflight

Status: prerequisite investigation, not trading support. PEP is the native
Pepecoin proof-of-work blockchain, not an ERC-20 token. This change does not
register a coin ID, enable offers, install a daemon, or establish liquidity.

## Sources inspected

- BasicSwap: `5471e609b9fbcba1a528dac60e2e06fc2f1a8ca4`.
- Pepecoin Core: `4fb5a0cd930c0df82c88292e973a7b7cfa06c4e8`.
- [Pepecoin Core](https://github.com/pepecoinppc/pepecoin).
- [BasicSwap DOGE adapter](https://github.com/basicswap/basicswap/blob/5471e609b9fbcba1a528dac60e2e06fc2f1a8ca4/basicswap/interface/doge/doge.py).
- [DOGE daemon preparation](https://github.com/basicswap/basicswap/blob/5471e609b9fbcba1a528dac60e2e06fc2f1a8ca4/basicswap/interface/doge/core.py)
  currently uses tecnovert's Dogecoin 23.2.1 builds. Stock PEP Core is not that
  daemon and cannot inherit its RPC behavior merely by changing prefixes.

## Verified network parameters

From Pepecoin `src/chainparams.cpp`, `src/chainparamsbase.cpp`,
`src/amount.h`, and `src/validation.cpp` at the revision above:

| Parameter | Mainnet | Testnet | Regtest |
| --- | --- | --- | --- |
| RPC port | 33873 | 44873 | 18332 |
| P2PKH prefix | 56 | 113 | 111 |
| P2SH prefix | 22 | 196 | 196 |
| WIF prefix | 158 | 241 | 239 |
| Data subdirectory | none | testnet3 | regtest |
| Target block spacing, seconds | 60 | 60 | 1 |

Eight decimal places; message magic `Pepecoin Signed Message:\n`.
`MAX_MONEY` is 10,000,000,000 PEP as a monetary range bound, not a supply cap.
Do not substitute ticker, port, testnet directory, or derivation constants from
Dogecoin without checking them. A PEP-specific BIP44 choice remains to be verified
before defining deterministic wallet paths.

## Current compatibility gaps

The inherited BasicSwap BTC interface expects RPCs absent from stock PEP's
registered RPC table at the inspected revision:

| BasicSwap operation | PEP Core difference | Work required |
| --- | --- | --- |
| `listwallets`, `createwallet` | Older single-wallet API | Dedicated wallet lifecycle |
| `sethdseed` | No equivalent registered RPC | Implement and validate deterministic initialization/recovery, or explicitly design an independent-wallet mode |
| `getwalletinfo.hdseedid` | Uses `hdmasterkeyid` | Verify semantics and seed identity checks |
| `getaddressinfo` | `validateaddress` available | Normalize ownership and watch-only fields |
| `signrawtransactionwithwallet` | `signrawtransaction` available | Override signing and verify complete signatures |
| `getbalances` | Older wallet/balance API | Normalize spendable balances |
| `rescanblockchain` | No equivalent registered RPC | Implement reliable watch-only discovery and restart recovery |

RPC renaming alone does not establish compatibility. In particular, silently
skipping seed initialization would misrepresent what a BasicSwap seed restores.
Two viable designs need evaluation: a tested legacy PEP adapter, or a maintained
PEP daemon build with the needed wallet RPCs. The latter should be a separate
reviewed Core change with reproducible binaries and verified release signatures.

## Pair scope

The closest existing path treats PEP as a non-SegWit scriptless-side coin, as
BasicSwap currently treats DOGE. This is a proposed protocol role, not a claim
that PEP has no scripting capabilities.

BasicSwap's `validateSwapType` rejects a pair when both coins require the
scriptless/non-SegWit role. Under this design, BTC/PEP and LTC/PEP are initial
test targets in both directions. PEP/DOGE is not supported by simply adding
PEP to the same registry. Do not advertise it without separate protocol work.

## Read-only node preflight

Use a running PEP node and its matching `pepecoin-cli`. Credentials stay in the
node's local configuration; the checker never prints daemon error output.

```sh
python3 scripts/check_pepecoin_compatibility.py --cli /path/to/pepecoin-cli --network regtest --datadir /path/to/isolated-pep-regtest
```

This executes only `getblockhash 0` and `help`, verifies genesis, and reports
missing methods for direct reuse of the current DOGE adapter. It never creates
a wallet, imports a key, signs, or broadcasts. Exit 0 means only this limited RPC
preflight passed; exit 1 means blocked; exit 2 means the node could not be queried.
The output always states that swap safety has not been validated.

## Required implementation and acceptance work

1. Agree the wallet/daemon architecture above, and allocate an upstream coin ID.
2. Add network parameters, interface creation, startup/shutdown handling, daemon
   preparation and signature verification, and explicit protocol eligibility.
3. Validate address/WIF encoding, integer amounts, fee and dust behavior, legacy
   transaction serialization/signing, wallet ownership, and watch-only discovery.
4. Run isolated regtest BTC/PEP and LTC/PEP swaps in both directions, including
   leader/follower failure, refunds, recovery, restarts, and seed restoration.
   Assert that unsupported PEP/DOGE offers are rejected.
5. Add UI names/logos and optional price mapping only after the protocol path
   works; market prices must not be confused with executable offers.
6. Submit the tested support PR for upstream review. Following merge/release,
   liquidity operators must upgrade, fund PEP wallets, and publish offers.

No live swap tests have been performed for this proposal. The accompanying
dependency-free tests validate the checker, not Pepecoin trading support.

## Haze Wallet boundary

The reviewed Haze build integrates with a BasicSwap node via JSON API. Adding a
PEP entry in that web client cannot add PEP to the BasicSwap protocol. Its local
request board also does not supply executable network offers. Funding custody
and user-wallet association are a separate integration concern; this proposal
does not claim that a shared BasicSwap server signs from individual browser keys.
