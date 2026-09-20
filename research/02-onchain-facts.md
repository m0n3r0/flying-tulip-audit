# Flying Tulip — Verified On-Chain Facts

Values were first read live from public RPCs on **2026-09-02** and re-verified on
**2026-09-20** (raw JSON-RPC `eth_call`/`eth_getCode` on all five chains). Where the two
reads differ, the 2026-09-20 value is authoritative and the change is noted. Reproduce
with the commands in `scripts/`.

Canonical FT token: **`0x5DD1A7A369e8273371d2DBf9d83356057088082c`**
(identical address — and identical 10,002-byte runtime — on Ethereum, BSC, Base,
Avalanche, Sonic).

---

## 1. Supply — docs say 10B, chain says 850M and shrinking

`totalSupply()` per chain (2026-09-20):

| Chain | FT total (2026-09-20) | FT total (2026-09-02) |
|---|---|---|
| Ethereum | 847,330,958.55 | 1,196,643,745.86 |
| Sonic | 2,714,977.56 | 1,979,127.96 |
| Base | 16,622.64 | 16,622.64 |
| BNB Chain | 241.37 | 241.37 |
| Avalanche | 0.00 | 0.00 |
| **Total (EVM)** | **850,062,800.12 FT** | **1,198,639,737.83 FT** |

**Stated max supply: 10,000,000,000 FT.** Supply fell **−348,576,937.71 FT (−29%) in 18
days**, concentrated on Ethereum.

The docs assert *"maximum supply of 10 billion, minted at deployment"*, *"no
additional minting"*, and *"totalSupply stays at 10B, only the split between
circulating and non-circulating supply changes."* None of that matches the chain: supply
was 1.199B at first read and is 850M now.

**Where the ~8.8B went — disclosed on X, not in the docs.** The founder stated on
2026-08-03: *"Burned unallocated 9bn FT bringing FDV to 100m"*, and on 2026-08-10:
*"8.79bn unallocated FT permanently burned."* The burn is real and publicly acknowledged
([posts](https://x.com/AndreCronjeTech/status/2084252341222396227));
the documentation was never updated. Burns are ongoing: the 18-day −348.6M move combines
further unallocated burns from the configurator's own balance with revenue-funded
buyback-and-burn (founder, 2026-09-17: *"From bb&burn, not non-circ."*; cumulative
buyback $1.2M per founder, 2026-09-18).

At the stated **10 FT per $1** rate, 850.06M FT implies **≈ $85.0M of contributions** if
every token is issued — still *below* the publicly claimed **$200M private round**. The
founder's own figure is lower again: *"$50.95m in PUT backing capital"* (2026-08-10),
consistent with issued supply only (850M − 330M configurator-held ≈ 520M FT ≈ $52M).

> Method note: mint/burn history is still not reconstructable from public RPCs
> (`eth_getLogs` capped at 50k blocks), but the founder's public statements resolve the
> direction of the discrepancy. What remains undocumented is the *reconciliation*: no
> official doc explains 10B → 850M.

```mermaid
flowchart TB
    DOC["DOCS - stale<br/>maximum supply 10,000,000,000 FT<br/>minted at deployment<br/>no additional minting<br/>totalSupply stays at 10B"]

    CHAIN["CHAIN - totalSupply summed over 5 EVM deployments<br/>2026-09-02: 1,198,639,737.83<br/>2026-09-20: 850,062,800.12"]

    BURN["RECONCILIATION - disclosed on X only<br/>2026-08-03: burned unallocated 9bn FT<br/>2026-08-10: 8.79bn permanently burned<br/>ongoing revenue-funded bb and burn"]

    GAP["DOCS GAP<br/>no official document explains<br/>10B to 850M"]

    RATE["Rate: 10 FT per 1 dollar<br/>850M implies approx 85M committed<br/>founder states 50.95M PUT backing<br/>both BELOW the claimed 200M round"]

    DOC --> GAP
    CHAIN --> BURN
    BURN --> RATE
    CHAIN --> RATE

    classDef claim fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class DOC claim
    class CHAIN,BURN good
    class RATE neutral
    class GAP bad
```

### Abandoned test deployment
`0x9B15Cce2D9C396B8B840C167374DCe873b2CcE6d` (Sonic) is in the repo's own
`deployments/sonic-mainnet/FT.json`. State as of 2026-09-02 (not re-checked 2026-09-20):
- `name()` = **"Test name"**, `symbol()` = **"Test symbol"**
- `totalSupply()` = **9,999,995,990 FT**
- `paused()` = **true**, `owner()` = `0xa801864d0d24686b15682261aa05d4e1e6e5bd94` (an EOA, not the multisig)

A 10B-unit "Test name" deployment is permanently live on Sonic mainnet. Hygiene issue
only — it is not real FT supply — but it is exactly the kind of stale artefact that
gets picked up by token trackers.

## 2. Distribution — Ethereum (99.9% of supply is here)

`holdersCount` = **688** (2026-09-02; not re-measured). Top holders (2026-09-20):

| # | Address | Balance (FT, 2026-09-20) | Share | Identity |
|---|---|---|---|---|
| 1 | `0x22246a9183ce2ce6e2c2a9973f94aea91435017c` | 330,000,000 | **38.95%** | the `configurator` (same address verified at first read; 648,033,208 on 2026-09-02 — its balance absorbed most of the 18-day burn) |
| 2 | `0xba49d0ac42f4fba4e24a8677a22218a4df75ebaa` | 427,039,967 | **50.40%** | unidentified contract (141-byte runtime; not a Safe; likely `PutManager`) |
| 3 | `0xaec73da67132a45d93e20cddf1b8cd13e2580870` | 50,000,000 | 5.90% | unknown (2026-09-02; not re-measured) |
| 4 | `0x4577286a6082df1f99adbf790c4104dd90abefbc` | 30,000,000 | 3.54% | unknown (2026-09-02; not re-measured) |
| 5 | `0x4de4043a9c6990b414bdcc106f15ef8ab3300c13` | 10,000,000 | 1.18% | unknown (2026-09-02; not re-measured) |

**Top 2 addresses control 89.35% of supply** (89.95% at first read).

```mermaid
flowchart TB
    SUP["Total measured supply 2026-09-20<br/>850,062,800 FT"]

    SUP --> CFG["configurator Safe 0x22246a<br/>330,000,000 FT = 38.95%<br/>was 648M before the burns"]
    SUP --> PM["unidentified contract 0xba49d0<br/>likely PutManager - 427,039,967 FT = 50.40%"]
    SUP --> REST["remaining holders<br/>~10% incl 50M + 30M + 10M unidentified"]
    SUP --> FLOAT["TRADEABLE FLOAT<br/>~20.7M FT ≈ 2M dollars<br/>founder concurs: 2m mcap"]

    CFG --> CFG_N["The same role that is<br/>EXEMPT FROM THE PAUSE<br/>holds 39% of supply"]
    PM --> PM_N["Closed source<br/>no public audit"]
    FLOAT --> FLOAT_N["~265K/day volume<br/>688 holders"]

    FLOAT_N --> PRICE["This thin float sets the price<br/>that marks the 'unlimited upside'<br/>of the other ~97%"]

    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    classDef closed fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
    class SUP,REST neutral
    class CFG,CFG_N,FLOAT,FLOAT_N,PRICE bad
    class PM,PM_N closed
```

## 3. Market data (Ethereum, 2026-09-20)

| Metric | Value | As of |
|---|---|---|
| Price | **$0.1079** (14 pairs, DexScreener) | 2026-09-20 |
| 24h volume | **$267,438** | 2026-09-20 |
| `availableSupply` (float) | **20,668,218 FT** ≈ **$2.10M** — founder concurs: *"$2m mcap"* (X, 2026-09-18) | 2026-09-02 |
| Fully-diluted (850.06M × price) | **≈ $91.7M** | 2026-09-20 |
| Holders | **688** | 2026-09-02 |
| Contract created | 2025-11-17 (creator `0x44820497f8fe95a258a9522f0de2c04ab2bc3da3`) | — |

**FDV ≈ $91.7M vs. the $1B headline private-round valuation — roughly an 11x gap.**
Note the founder's own "$48m fdv" (X, 2026-09-18) is inconsistent with market data
(850.06M × $0.108) by about 2x, while his "$2m mcap" matches the float exactly.
Daily volume is ~0.13% of the claimed $200M private round.

## 4. Privileged roles

| Role | Address | Type | Powers |
|---|---|---|---|
| `owner()` | `0x1118e1c057211306a40A4d7006C040dbfE1370Cb` | Gnosis Safe, **3-of-5** | `setPaused`, `setName`, `setSymbol`, `transferConfigurator` |
| `configurator()` | `0x22246a9183ce2ce6e2c2a9973f94aea91435017c` | Gnosis Safe, **3-of-4** | `setPaused`, `transferConfigurator`, **pause-bypass transfers** |

Re-verified 2026-09-20: `owner()` returns `0x1118e1c0…370Cb` on **all five chains**. The
`configurator()` read reverted on re-check, so role continuity is inferred from the #1
holder balance at the same address rather than re-read directly.

### Signer overlap — the two roles are not independent

```
configurator Safe (0x22246a, 3-of-4):        owner Safe (0x1118e1, 3-of-5):
  0xb7b543337539219a5a1326acb71dba8bba408bc8   0xb7b543337539219a5a1326acb71dba8bba408bc8  <- same
  0x3c42749709bf354b3ae0db29fd2dd88089b21b4e   0x3c42749709bf354b3ae0db29fd2dd88089b21b4e  <- same
  0x09e2b49280f1879172b2c3345d08896921707881   0x09e2b49280f1879172b2c3345d08896921707881  <- same
  0xd0ca88388d1732594d611535314e9b6745396f5a   0xd0ca88388d1732594d611535314e9b6745396f5a  <- same
                                               0xf9e5af16243041ce3141284d225cafc0fc749a10
```

**4 of 5 owner signers are also configurator signers.** The "separation of duties"
between the role that can pause (`owner`) and the role that is exempt from the pause
(`configurator`) is largely cosmetic. There is no independent check on the configurator.

```mermaid
flowchart TB
    subgraph OWN["owner Safe 0x1118e1 - 3 of 5"]
        O1["0xb7b54333"]
        O2["0x3c427497"]
        O3["0x09e2b492"]
        O4["0xd0ca8838"]
        O5["0xf9e5af16<br/>owner only"]
    end

    subgraph CFG["configurator Safe 0x22246a - 3 of 4"]
        C1["0xb7b54333"]
        C2["0x3c427497"]
        C3["0x09e2b492"]
        C4["0xd0ca8838"]
    end

    O1 <-->|"same signer"| C1
    O2 <-->|"same signer"| C2
    O3 <-->|"same signer"| C3
    O4 <-->|"same signer"| C4

    OWN --> POW_O["Powers: setPaused<br/>setName, setSymbol<br/>transferConfigurator"]
    CFG --> POW_C["Powers: setPaused<br/>transferConfigurator<br/>PAUSE-BYPASS TRANSFERS"]

    CFG --> HOLD["Also holds 330,000,000 FT<br/>38.95% of supply"]

    POW_O --> FX["Consequence<br/>The role that can freeze everyone else<br/>and the role exempt from the freeze<br/>are controlled by 4 shared keys<br/>No independent check exists"]

    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class O5 neutral
    class C1,C2,C3,C4,O1,O2,O3,O4 warn
    class POW_C,HOLD,FX bad
    class POW_O neutral
    style OWN fill:#f1f5f9,stroke:#64748b,color:#0f172a
    style CFG fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
```

## 5. Pause state

`paused()` = **false** on Ethereum, BSC, Base, Avalanche and Sonic (canonical `0x5DD1…`),
re-verified 2026-09-20.

Note the contract is **deployed paused** (`_pause()` in the constructor), so it had to
be unpaused by an insider after the 10B premint to the configurator.

## 6. Hardcoded role constants (`ft/utils/constants.ts`)

```ts
STANDARD_FT_DELEGATE     = 0x22246a9183ce2ce6e2c2a9973f94aea91435017c
STANDARD_FT_CONFIGURATOR = 0x22246a9183ce2ce6e2c2a9973f94aea91435017c   // same key
STANDARD_FINAL_OWNER     = 0x1118e1c057211306a40A4d7006C040dbfE1370Cb
```

Delegate and configurator are the **same address on every chain** — one 3-of-4 Safe
across Ethereum, BSC, Base, Avalanche, Sonic. Correlated-key risk: a single
compromise affects all deployments simultaneously. (Env overrides were added per
their own finding I-2, but the defaults hardcode one key.)

## 7. Correctness checks that PASSED

- `_EIP712_DOMAIN_TYPEHASH` = `0x8b73c3c6…b39400f` — **matches**
  `keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")`
- `_PERMIT_TYPEHASH` = `0x6e71edae…d6126c9` — **matches**
  `keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)")`
- `DOMAIN_SEPARATOR()` includes `block.chainid` + `address(this)` → no cross-chain permit replay
- Nonce is consumed in both `permit` overloads → no replay; ERC-1271 path reentrancy
  is bounded by recursion depth/gas
- OFT credit/debit paths are correctly exempted from the pause (`endpoint` caller check)
