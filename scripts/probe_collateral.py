#!/usr/bin/env python3
"""Enumerate collateral + oracle prices on ethereum or sonic. Direct probes."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rpc_probe import rpc, call, decode_addr, decode_uint

CHAINS = sys.argv[1:]

# standard ERC20 selectors
SYMBOL = "0x95d89b41"
DECIMALS = "0x313ce567"

for CHAIN in CHAINS:
    PM = "0xba49d0ac42f4fba4e24a8677a22218a4df75ebaa"
    print(f"\n===== {CHAIN} =====")
    oracle = decode_addr(call(CHAIN, PM, "0xb18b78dd"))
    print(f"PutManager: {PM}")
    print(f"oracle (getOracleAddress): {oracle}")

    # oracle params
    ftPerUSD_raw = call(CHAIN, oracle, "0xe23d22ca")
    ftPerUSD = decode_uint(ftPerUSD_raw)
    print(f"oracle ftPerUSD() raw={ftPerUSD_raw} -> {ftPerUSD} (scale 1e8) = {ftPerUSD/1e8:.6f} FT per USD")

    idx = decode_uint(call(CHAIN, PM, "0xfe93de1f"))
    print(f"collateralIndex={idx}")
    GCOLL = "0x2a62a490"
    for i in range(idx):
        tok = decode_addr(call(CHAIN, PM, GCOLL + i.to_bytes(32, "big").hex()))
        # symbol
        sym = None
        try:
            sraw = call(CHAIN, tok, SYMBOL)
            sbytes = bytes.fromhex(sraw[2:])
            sym = sbytes.rstrip(b"\x00").decode("utf-8", "replace")
        except Exception as e:
            sym = f"ERR {e}"
        dec = None
        try:
            dec = decode_uint(call(CHAIN, tok, DECIMALS))
        except Exception as e:
            dec = f"ERR {e}"
        price = None
        try:
            p = call(CHAIN, oracle, "0xb3596f07" + tok[-40:].rjust(64, "0"))
            price = decode_uint(p) / 1e8
        except Exception as e:
            price = f"ERR {e}"
        print(f"  getCollateral({i}) = {tok}  sym={sym}  decimals={dec}  oracle.getAssetPrice={price} USD")