#!/usr/bin/env python3
"""
probe_avax_strategy.py — Is HyphaStAVAXStrategy deployed in the live ftPUT system?

Answers the S-01 deployment question (findings/04, follow-up issue #8) against live
state, read-only eth_calls only (no transactions):

  1. For every chain with a PutManager proxy, read the collateral registry
     (collateralIndex / getCollateral) and check whether wAVAX is registered.
  2. For every registered collateral, read its vault (vaults(token)) and enumerate
     the vault's strategies (numberOfStrategies / strategies(i)).
  3. Classify each strategy by probing venue-specific getters:
       Hypha markers: staking() / withdrawQ() / stAVAX()  (public immutables of
                      HyphaStAVAXStrategy only; see contracts/strategies/
                      HyphaStAVAXStrategy.sol L74-76 and its ERC20 name
                      "Flying Tulip Hypha stAVAX")
       Aave marker:   pool()  (AaveStrategy)
  4. Verdict: whether a Hypha-marked strategy is registered anywhere.

READ AS (chain, address): the same deployer convention was used across chains, so
the SAME ADDRESS can be a different contract on another chain (e.g. 0x9d96bac8… is
the wAVAX vault on AVAX and the wBNB strategy on BSC).

Robustness: a transport error (rate limit / 5xx / 403) falls back to the chain's
other RPCs; a revert is a legitimate negative answer. A failed call never aborts
the run — missing data shows up as empty fields in the JSON.

Usage:
  python3 scripts/probe_avax_strategy.py [out.json]
"""
import json, sys, time, urllib.request

PM    = "0xba49d0ac42f4fba4e24a8677a22218a4df75ebaa"   # PutManager proxy (same addr, all chains)
WAVAX = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7"   # canonical wAVAX (Avalanche)
ZERO  = "0x0000000000000000000000000000000000000000"

CHAIN_RPCS = {
    "eth":   ["https://ethereum-rpc.publicnode.com", "https://eth.llamarpc.com", "https://1rpc.io/eth", "https://eth.drpc.org", "https://rpc.flashbots.net"],
    "bsc":   ["https://bsc-dataseed.binance.org", "https://bsc-rpc.publicnode.com", "https://1rpc.io/bnb"],
    "base":  ["https://mainnet.base.org", "https://base-rpc.publicnode.com", "https://1rpc.io/base", "https://base.drpc.org", "https://base.llamarpc.com"],
    "avax":  ["https://api.avax.network/ext/bc/C/rpc", "https://avalanche-c-chain-rpc.publicnode.com", "https://1rpc.io/avax/c"],
    "sonic": ["https://rpc.soniclabs.com", "https://sonic-rpc.publicnode.com", "https://1rpc.io/sonic"],
}

SEL = {
    "collateralIndex":    "0xfe93de1f",
    "getCollateral":      "0x2a62a490",
    "vaults":             "0xa622ee7c",
    "numberOfStrategies": "0x0956e5a6",
    "strategies":         "0xd574ea3d",
    "name":               "0x06fdde03",
    "token":              "0xfc0c546a",
    "positionToken":      "0x5037b7e9",
    "staking":            "0x4cf088d9",   # Hypha-only public getter
    "withdrawQ":          "0xd21cd5e5",   # Hypha-only public getter
    "stAVAX":             "0xa0b814b5",   # Hypha-only public getter
    "pool":               "0x16f0115b",   # AaveStrategy public getter
}

def rpc_call(rpc_url, method, params, timeout=15):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(rpc_url, data=payload,
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "Mozilla/5.0 (ftput-probe)",
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def call(rpc_url, to, data):
    """eth_call. Returns (result, status) with status in 'ok' / 'revert' / 'error'."""
    try:
        res = rpc_call(rpc_url, "eth_call", [{"to": to, "data": data}, "latest"])
    except Exception:
        return None, "error"
    if "result" in res:
        return res["result"], "ok"
    err = res.get("error") or {}
    msg = (str(err.get("message", "")) + " " + str(err.get("data", ""))).lower()
    if "revert" in msg or err.get("code") == 3:
        return None, "revert"
    return None, "error"

def call_chain(chain, primary, to, data):
    """call() with fallback: transport errors try the chain's other RPCs.
    A revert is returned as a legitimate None immediately."""
    r, st = call(primary, to, data)
    if st != "error":
        return r
    for url in CHAIN_RPCS[chain]:
        if url == primary:
            continue
        r, st = call(url, to, data)
        if st != "error":
            return r
    return None

def get_code_chain(chain, primary, addr):
    for url in [primary] + [u for u in CHAIN_RPCS[chain] if u != primary]:
        try:
            res = rpc_call(url, "eth_getCode", [addr, "latest"])
            if "result" in res:
                return res["result"] or "0x"
        except Exception:
            continue
    return None

def work_rpc(chain):
    for url in CHAIN_RPCS[chain]:
        try:
            res = rpc_call(url, "eth_blockNumber", [])
            if "result" in res:
                return url, int(res["result"], 16)
        except Exception as e:
            print(f"  [{chain}] x {url} ({e})")
    return None, 0

def dec_uint(h):
    if h in (None, "0x"): return 0
    return int(h, 16)

def dec_addr(h):
    if h in (None, "0x") or len(h) < 42: return None
    a = "0x" + h[-40:]
    return None if a.lower() == ZERO else a

def dec_str(h):
    if h in (None, "0x"): return ""
    b = bytes.fromhex(h[2:])
    if len(b) < 64: return ""
    try:
        off = int.from_bytes(b[:32], "big")
        ln = int.from_bytes(b[off:off+32], "big")
        return b[off+32:off+32+ln].decode("utf-8", errors="replace")
    except Exception:
        return ""

def enc_uint(i): return f"{i:064x}"
def enc_addr(a): return a[2:].lower().rjust(64, "0")

def classify(chain, rpc_url, strat):
    """Probe venue markers. A revert / absent answer means the marker is absent."""
    markers = {}
    for m in ("staking", "withdrawQ", "stAVAX"):
        markers[m] = dec_addr(call_chain(chain, rpc_url, strat, SEL[m])) is not None
    pool = dec_addr(call_chain(chain, rpc_url, strat, SEL["pool"]))
    if any(markers.values()):
        return "HYPHA", markers, pool
    if pool:
        return "aave", markers, pool
    return "unclassified", markers, pool

def probe_chain(chain):
    print(f"\n=== {chain.upper()} ===")
    rpc_url, block = work_rpc(chain)
    if not rpc_url:
        print("  NO WORKING RPC")
        return {"chain": chain, "rpc": None}
    print(f"  via {rpc_url} (block {block:,})")

    if get_code_chain(chain, rpc_url, PM) in ("0x", None):
        print("  PutManager: no code")
        return {"chain": chain, "rpc": rpc_url, "block": block, "putmanager": False}

    n = dec_uint(call_chain(chain, rpc_url, PM, SEL["collateralIndex"]))
    tokens = [dec_addr(call_chain(chain, rpc_url, PM, SEL["getCollateral"] + enc_uint(i))) for i in range(n)]
    wavax_registered = any(t and t.lower() == WAVAX.lower() for t in tokens)
    print(f"  collaterals: {n}" + ("   [wAVAX REGISTERED]" if wavax_registered else ""))

    out = {"chain": chain, "rpc": rpc_url, "block": block, "putmanager": True,
           "collateral_index": n, "wavax_registered": wavax_registered, "vaults": []}

    for t in tokens:
        if not t:
            continue
        v = dec_addr(call_chain(chain, rpc_url, PM, SEL["vaults"] + enc_addr(t)))
        entry = {"token": t, "vault": v, "strategies": []}
        if not v:
            print(f"    {t[:10]}.. no vault registered")
        elif get_code_chain(chain, rpc_url, v) in ("0x", None):
            print(f"    {t[:10]}.. vault {v[:10]}.. no code")
        else:
            m = dec_uint(call_chain(chain, rpc_url, v, SEL["numberOfStrategies"]))
            if m == 0:
                print(f"    {t[:10]}.. vault {v[:10]}.. 0 strategies")
            for j in range(m):
                s = dec_addr(call_chain(chain, rpc_url, v, SEL["strategies"] + enc_uint(j)))
                if not s:
                    continue
                nm = dec_str(call_chain(chain, rpc_url, s, SEL["name"]))
                cls, markers, pool = classify(chain, rpc_url, s)
                entry["strategies"].append({"address": s, "name": nm, "class": cls,
                                            "hypha_markers": markers, "pool": pool})
                flag = "   <<< HYPHA" if cls == "HYPHA" else ""
                print(f"    {t[:10]}.. vault {v[:10]}.. strat {s}  {cls:12s} {nm!r}{flag}")
        out["vaults"].append(entry)
    return out

def main():
    date = time.strftime("%Y-%m-%d", time.gmtime())
    out_path = sys.argv[1] if len(sys.argv) > 1 else f"research/probe_avax_strategy_{date}.json"
    results = {"probed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "putmanager_proxy": PM, "wavax": WAVAX, "chains": {}}
    hypha_hits, wavax_chains = [], []
    for chain in ["eth", "bsc", "base", "avax", "sonic"]:
        c = probe_chain(chain)
        results["chains"][chain] = c
        if c.get("wavax_registered"):
            wavax_chains.append(chain)
        for v in c.get("vaults", []):
            for s in v["strategies"]:
                if s["class"] == "HYPHA":
                    hypha_hits.append({"chain": chain, "address": s["address"]})
    results["verdict"] = {
        "hypha_registered_anywhere": bool(hypha_hits),
        "hypha_hits": hypha_hits,
        "wavax_registered_chains": wavax_chains,
    }
    print("\n================= VERDICT =================")
    print(f"  wAVAX registered on:   {wavax_chains or 'no chain'}")
    print(f"  Hypha strategy found:  {hypha_hits if hypha_hits else 'NO - not registered in any live vault'}")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved -> {out_path}")

if __name__ == "__main__":
    main()