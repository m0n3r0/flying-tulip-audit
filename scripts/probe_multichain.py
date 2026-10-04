#!/usr/bin/env python3
"""
probe_multichain.py — Re-probe Flying Tulip addresses across 5 EVM chains.

Reconciled address set (from research/02-onchain-facts.md + findings/04):
  FT token:        0x5DD1A7A369e8273371d2DBf9d83356057088082c  (all 5 chains)
  PutManager:      0xba49d0ac42f4fba4e24a8677a22218a4df75ebaa  (ETH + Sonic)
  Safe (treasury): 0x1118e1c057211306a40A4d7006C040dbfE1370Cb  (all 5 chains)
  PM msig (ETH):   0x3518db98cb1fcb19e0c430b3e7f7f74b2a354707  (ETH only)

Per-chain fallback RPCs tried in order until one responds.

Usage:
  python3 scripts/probe_multichain.py research/probe_results_2026-10-04.json
"""
import json, sys, time, urllib.request, urllib.error

# ── Reconciled address set ────────────────────────────────────────────────────
ADDRESSES = {
    "FT_token":        "0x5DD1A7A369e8273371d2DBf9d83356057088082c",
    "PutManager":      "0xba49d0ac42f4fba4e24a8677a22218a4df75ebaa",
    "Safe_treasury":   "0x1118e1c057211306a40A4d7006C040dbfE1370Cb",
    "PM_msig_ETH":     "0x3518db98cb1fcb19e0c430b3e7f7f74b2a354707",
}

# ── Per-chain RPC fallbacks (tried in order) ─────────────────────────────────
CHAIN_RPCS = {
    "eth": [
        "https://ethereum-rpc.publicnode.com",
        "https://eth.llamarpc.com",
        "https://rpc.ankr.com/eth",
        "https://cloudflare-eth.com",
        "https://1rpc.io/eth",
    ],
    "bsc": [
        "https://bsc-dataseed.binance.org",
        "https://bsc-rpc.publicnode.com",
        "https://1rpc.io/bnb",
    ],
    "base": [
        "https://mainnet.base.org",
        "https://base-rpc.publicnode.com",
        "https://1rpc.io/base",
    ],
    "avax": [
        "https://api.avax.network/ext/bc/C/rpc",
        "https://avalanche-c-chain-rpc.publicnode.com",
        "https://1rpc.io/avax/c",
    ],
    "sonic": [
        "https://rpc.soniclabs.com",
        "https://sonic-rpc.publicnode.com",
        "https://1rpc.io/sonic",
    ],
}

# ── ABI selectors ─────────────────────────────────────────────────────────────
SEL = {
    "totalSupply":  "0x18160ddd",
    "balanceOf":    "0x70a08231",
    "name":         "0x06fdde03",
    "paused":       "0x5c975abb",
    "owner":        "0x8da5cb5b",
    "ftOfferingSupply": "0x24bb4088",
    "ftPut":        "0x1f538165",
}

def rpc_call(rpc_url, method, params, timeout=10):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(rpc_url, data=payload,
        headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def try_rpc(chain, method, params):
    """Try each RPC for the chain until one works. Returns (result, rpc_url) or (None, None)."""
    for url in CHAIN_RPCS[chain]:
        try:
            res = rpc_call(url, method, params)
            if "result" in res:
                return res["result"], url
        except Exception as e:
            print(f"  [{chain}] ✗   {url}  ({e})")
            time.sleep(0.3)
    return None, None

def eth_call(rpc_url, to, data):
    return rpc_call(rpc_url, "eth_call", [{"to": to, "data": data}, "latest"])

def decode_uint(hex_str):
    if hex_str in (None, "0x"): return 0
    return int(hex_str, 16)

def decode_bytes(hex_str):
    if hex_str in (None, "0x"): return b""
    return bytes.fromhex(hex_str[2:])

def decode_string(hex_str):
    """Decode ABI-encoded string from eth_call result."""
    if hex_str in (None, "0x"): return ""
    b = bytes.fromhex(hex_str[2:])
    if len(b) < 64: return ""
    try:
        off = int.from_bytes(b[:32], 'big')
        ln   = int.from_bytes(b[off:off+32], 'big')
        return b[off+32:off+32+ln].decode('utf-8', errors='replace')
    except Exception:
        return ""

def probe_chain(chain):
    print(f"\n=== {chain.upper()} ===")
    # Get a working RPC
    _, rpc_url = try_rpc(chain, "eth_blockNumber", [])
    if not rpc_url:
        print(f"  NO WORKING RPC for {chain}")
        return {"chain": chain, "rpc": None, "addresses": {}}

    bn = int(rpc_url and "" or "", 16) if False else None
    # re-fetch block number to get actual value
    res, _ = try_rpc(chain, "eth_blockNumber", [])
    block = int(res, 16) if res else 0
    print(f"  [{chain}] OK  {rpc_url}  (block={block:,})")

    addrs = {}
    for label, addr in ADDRESSES.items():
        # Skip ETH-only address on non-ETH chains
        if label == "PM_msig_ETH" and chain != "eth":
            continue
        info = {"address": addr}

        # 1) bytecode
        code, _ = try_rpc(chain, "eth_getCode", [addr, "latest"])
        code_bytes = decode_bytes(code)
        info["bytecode_size"] = len(code_bytes)
        info["bytecode"] = "0x" + code_bytes.hex() if code_bytes else "0x"

        if not code_bytes:
            info["note"] = "no contract (EOA or empty)"
            addrs[label] = info
            print(f"  {label:20s} {addr}  →  0 bytes (no contract)")
            continue

        # 2) name()
        res, _ = try_rpc(chain, "eth_call",
            [{"to": addr, "data": SEL["name"]}, "latest"])
        name = decode_string(res)
        if name:
            info["name"] = name

        # 3) totalSupply()
        res, _ = try_rpc(chain, "eth_call",
            [{"to": addr, "data": SEL["totalSupply"]}, "latest"])
        if res:
            info["totalSupply"] = decode_uint(res)

        # 4) paused()
        res, _ = try_rpc(chain, "eth_call",
            [{"to": addr, "data": SEL["paused"]}, "latest"])
        if res:
            info["paused"] = decode_uint(res) != 0

        # 5) owner()
        res, _ = try_rpc(chain, "eth_call",
            [{"to": addr, "data": SEL["owner"]}, "latest"])
        if res and res != "0x":
            raw = res[2:]
            info["owner"] = "0x" + raw[-40:] if len(raw) >= 40 else "0x" + raw

        # 6) ftOfferingSupply() (PutManager only)
        if "PutManager" in label:
            res, _ = try_rpc(chain, "eth_call",
                [{"to": addr, "data": SEL["ftOfferingSupply"]}, "latest"])
            if res:
                info["ftOfferingSupply"] = decode_uint(res)

        # 7) balanceOf(FT_token) for non-FT addresses
        ft_addr = ADDRESSES["FT_token"]
        if addr != ft_addr:
            bal_data = SEL["balanceOf"] + ft_addr[2:].lower().rjust(64, "0")
            res, _ = try_rpc(chain, "eth_call",
                [{"to": ft_addr, "data": bal_data}, "latest"])
            if res:
                info["FT_balance"] = decode_uint(res)

        addrs[label] = info
        parts = [f"{label:20s} {addr}"]
        parts.append(f"  {len(code_bytes):,} B")
        if "name" in info: parts.append(f"  name={info['name']}")
        if "totalSupply" in info: parts.append(f"  supply={info['totalSupply']:,}")
        if "paused" in info: parts.append(f"  paused={info['paused']}")
        if "FT_balance" in info: parts.append(f"  FT={info['FT_balance']:,}")
        if "ftOfferingSupply" in info: parts.append(f"  offering={info['ftOfferingSupply']:,}")
        print("  ".join(parts))

    return {"chain": chain, "rpc": rpc_url, "block": block, "addresses": addrs}

def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "research/probe_results_2026-10-04.json"
    results = {"probed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "chains": {}}
    for chain in ["eth", "bsc", "base", "avax", "sonic"]:
        results["chains"][chain] = probe_chain(chain)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved → {out_path}")

if __name__ == "__main__":
    main()
