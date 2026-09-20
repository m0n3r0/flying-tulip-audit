#!/usr/bin/env python3
"""Live RPC probe for Flying Tulip deployed contracts. Stdlib-only."""
import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.keccak import keccak256, selector

RPC = {
    "ethereum": [
        "https://ethereum-rpc.publicnode.com",
        "https://eth.drpc.org",
        "https://cloudflare-eth.com",
        "https://rpc.mevblocker.io",
    ],
    "sonic": [
        "https://rpc.soniclabs.com",
        "https://sonic-rpc.publicnode.com",
    ],
}

def rpc(chain, method, params):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last = None
    for url in RPC[chain]:
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type":"application/json",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept":"application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.load(r)
        except Exception as e:
            detail = ""
            if isinstance(e, urllib.error.HTTPError):
                detail = e.read().decode(errors="replace")[:200]
            last = RuntimeError(f"{method} via {url}: {e} {detail}")
            continue
        if "error" in j:
            raise RuntimeError(f"{method} {params}: {j['error']}")
        return j["result"]
    raise last or RuntimeError(f"{method}: no endpoints for {chain}")

def get_code(chain, addr):
    return rpc(chain, "eth_getCode", [addr, "latest"])

def get_storage(chain, addr, slot):
    return rpc(chain, "eth_getStorageAt", [addr, slot, "latest"])

def call(chain, to, data):
    return rpc(chain, "eth_call", [{"to": to, "data": data}, "latest"])

def slot_of(s):
    h = int.from_bytes(keccak256(s.encode()), "big")
    return hex((h - 1) & ((1 << 256) - 1))

def u256(h):
    return int(h, 16)

def addr_of(h):
    return "0x" + h[-40:].lower()

def decode_addr(h):
    return "0x" + h[-40:].lower()

def decode_uint(h):
    return int(h, 16)

def decode_bool(h):
    return int(h, 16) != 0

if __name__ == "__main__":
    chain = sys.argv[1]
    addr = sys.argv[2].lower()
    print(f"=== {chain} proxy {addr} ===")
    impl_slot = slot_of("eip1967.proxy.implementation")
    admin_slot = slot_of("eip1967.proxy.admin")
    impl = decode_addr(get_storage(chain, addr, impl_slot))
    admin = decode_addr(get_storage(chain, addr, admin_slot))
    print(f"impl slot {impl_slot} -> {impl}")
    print(f"admin slot {admin_slot} -> {admin}")
    code = get_code(chain, addr)
    print(f"proxy runtime size: {len(code)//2 - 1} bytes")
    impl_code = get_code(chain, impl)
    print(f"impl runtime size: {len(impl_code)//2 - 1} bytes")
    print(f"impl code head: {impl_code[:130]}")
    print(f"impl code tail: {impl_code[-130:]}")
    # view calls
    calls = {
        "msig()": "0x7bb453bf",
        "configurator()": "0x2b507df8",
        "ftOracle()": "0x495d9741",
        "saleEnabled()": "0x71b9b646",
        "transferable()": "0x92ff0d31",
        "collateralIndex()": "0xfe93de1f",
        "paused()": "0x5c975abb",
        "getFTAddress()": "0x0b011758",
        "getOracleAddress()": "0xb18b78dd",
        "ftOfferingSupply()": "0x1b14773b",
        "ftAllocated()": "0x92a668ce",
        "delayMsig()": "0xadf5c4c1",
        "nextMsig()": "0x1e69aae8",
        "ftACL()": "0xc301ded3",
    }
    for name, sel in calls.items():
        try:
            raw = call(chain, addr, sel)
            if len(raw) == 66 and raw.startswith("0x000000000000000000000000"):
                val = decode_addr(raw)
            else:
                val = decode_uint(raw)
            print(f"{name:22s} {sel} -> {raw}  ({val})")
        except Exception as e:
            print(f"{name:22s} {sel} -> ERROR {e}")
