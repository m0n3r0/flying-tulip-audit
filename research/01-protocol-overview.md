# Flying Tulip — Protocol Overview

Andre Cronje's "full-stack on-chain exchange". Compiled from official docs
(`docs.flyingtulip.com`), the `flyingtulipdotcom` GitHub org, and on-chain state.

**Compiled:** 2026-09-02

---

## 1. Corporate / fundraising

| Item | Value | Source |
|---|---|---|
| Private seed round | **$200M** | docs, press |
| Headline token valuation | **$1B** | press (The Block) |
| Public sale ("Capital Allocation") | On-chain, at same valuation | docs |
| Primary issue rate | **10 FT per $1** → implied **$0.10 / FT** | docs |
| Stated max supply | **10,000,000,000 FT**, pre-minted at deployment | docs |

## 2. The core invention: the Perpetual PUT

Primary-sale FT is not delivered freely. It is locked into a **Perpetual PUT**
(an NFT, `ftPUT`) that grants an **evergreen, perpetual American put struck at par**.

Three mutually exclusive-ish choices, available at any time:

1. **Hold** — keep the PUT open. Principal protected at par; you watch FT upside but
   cannot realise it.
2. **Exit at par** — return FT, receive **the exact asset and amount originally
   contributed** (1,000 USDC in → 1,000 USDC out; 2 ETH in → 2 ETH out). PUT consumed.
   Nominal return: **0%**.
3. **Withdraw** — unlock FT so you can trade it. PUT is **invalidated forever**.
   The backing capital that was reserved for your Exit is released and used by the
   protocol to **market-buy and burn FT**.

```mermaid
flowchart TD
    START["Primary-sale FT<br/>locked in ftPUT"]

    START --> HOLD["1. HOLD<br/>keep the PUT open"]
    START --> EXIT["2. EXIT AT PAR<br/>return FT, receive the exact<br/>asset and amount contributed"]
    START --> WD["3. WITHDRAW<br/>unlock FT, tradeable"]

    HOLD --> HOLD_R["Principal protected at par<br/>You watch the upside<br/>but cannot realise it"]
    EXIT --> EXIT_R["Nominal return: 0%<br/>1,000 USDC in to 1,000 USDC out<br/>PUT consumed"]
    WD --> WD_R["PUT invalidated FOREVER<br/>Backing capital released<br/>protocol buys and burns FT"]

    WD_R --> TRADE["You now hold unprotected FT<br/>no PUT, no par floor"]

    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class START neutral
    class HOLD,HOLD_R good
    class EXIT,EXIT_R warn
    class WD,WD_R bad
    class TRADE bad
```

The critical property: **the three branches are one-way.** Branch 2 returns exactly your
principal and nothing more; branch 3 is the only way to realise upside and it destroys
the protection permanently. Protection and upside never coexist in the same hands at the
moment either matters — see [`W-01`](../findings/03-economics-high-yield.md#w-01--principal-protection-and-unlimited-upside-are-mutually-exclusive).

Key properties per docs:
- No vesting, no cliff, no lockup, no inflation, no additional minting.
- PUT attaches **only** to primary-issue FT. Secondary market FT has **no** PUT.
- "100% Capital Protection" — backing capital is **never spent**, kept in
  "safe, liquid, low-risk, no-leverage, no-bridging" yield positions.
- PUTs are tradeable on the `ftPUT` marketplace.

### Stated backing venues
- Major stables → **Aave v3**
- ETH → **stETH**
- SOL → **jupSOL**
- AVAX → **AVAX staking**
- USDe → **sUSDe**

## 3. Where "yield" supposedly comes from

Value does **not** flow to holders as cash. It flows as **buyback-and-burn**:

| Source | Description |
|---|---|
| A. Surplus backing-capital yield | **First call is the ecosystem budget** (salaries, marketing, infra, ops). Only the *surplus* is burned. |
| B. Protocol revenue & fees | ftUSD, Trade, Lend, Futures, Insurance revenue → buy FT "and, in many cases, burn it" |
| C. Released backing capital | When someone **Withdraws**, their reserved backing capital is spent buying + burning FT |

**Critical carve-out:** "Buyback-and-burn funded **only** by backing capital yield
**does not unlock anything**; they just reduce supply. **Revenue-funded** burns unlock
Foundation/Team/Incentives 1:1 at **40:40:20**."

```mermaid
flowchart TB
    subgraph SRC["Three stated funding sources"]
        A["A. Surplus backing-capital yield"]
        B["B. Protocol revenue and fees"]
        C["C. Backing capital released on Withdrawal"]
    end

    GROSS["Gross yield on backing capital<br/>~3.5% on ~120M = ~4.2M/yr"]

    GROSS --> OPEX{"Ecosystem budget<br/>takes FIRST CALL"}
    OPEX -->|"consumes most of it<br/>salaries, marketing, infra, ops"| RESID["Residual surplus<br/>~0.2M/yr = 0.16% of FDV"]
    OPEX -->|"if budget absorbs all"| ZERO["No surplus<br/>no buyback from this source"]

    RESID --> A
    A --> BURN["Buyback and burn FT"]
    B -->|"real but currently trivial<br/>265K/day volume, 688 holders"| BURN
    C ==>|"THE ONE THAT ACTUALLY SCALES"| BURN

    C -.->|"this is someone's PRINCIPAL,<br/>not yield"| NOTE["Transfer from leavers<br/>to remaining holders"]

    BURN --> UNLOCK{"Was the burn<br/>revenue-funded?"}
    UNLOCK -->|"yes"| UN40["Foundation / Team / Incentives<br/>unlock 1:1 at 40:40:20"]
    UNLOCK -->|"no - yield-funded only"| NONE["Unlocks nothing<br/>supply merely shrinks"]

    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class GROSS,B neutral
    class OPEX,RESID,BURN,UNLOCK warn
    class ZERO,A,C,NOTE,NONE bad
    class UN40 good
```

Note the shape of that: source **A** is a *residual* behind the operating budget, source
**B** is currently trivial, and source **C** — the one that scales — is principal, not
yield. See [`W-02`](../findings/03-economics-high-yield.md#w-02--the-buyback-is-funded-mainly-by-principal-not-by-yield)
and [`W-04`](../findings/03-economics-high-yield.md#w-04--the-yield-is-junior-to-the-teams-operating-budget).

## 4. Product suite

| Product | Claim |
|---|---|
| **ftUSD** | "Generates **7-8% APY** through delta-neutral strategies while maintaining a perfect $1 peg" (marketing site) |
| **sftUSD** | Staked ftUSD. Only staked version accrues yield. Rewards paid **in FT**, claimed from a rewards vault, **no auto-compounding** |
| **Trade** | Volatility-adaptive pools (ftDNMM) |
| **Futures** | "Oracle-free" perps, <500ms, soft liquidations |
| **Lend** | Any-asset-against-any-collateral, dynamic LTV |
| **Insure** | Pay-as-you-go protection |

### ftUSD reality check (from the docs themselves)
- **Stage 0 (live): ftUSD is just a USDC/USDT → Aave wrapper.** That is the *only*
  implemented on-chain strategy.
- Delta-neutral carry is **Stage 3+** — roadmap, not deployed.
- Docs' own benchmark table (Ethereum): Aave v3 USDC **3.50%**, Aave v3 USDT **2.56%**,
  Compound v3 USDC **3.52%**, Lido stETH **2.55%**.
- The **7-8% figure does not appear anywhere in the documentation.**
- Illustrative pipeline for the future delta-neutral leg: supply USDC → borrow S →
  stake to stS → *"loop collateral prudently (e.g. deposit stS back to the money
  market) to increase safety buffers and carry"* — i.e. **looping = leverage**.
- "Unstaked ftUSD receives no yield; proceeds accrue to the **protocol treasury**."
- "All net strategy yield and protocol fee revenue is collected by the protocol
  treasury; then **at treasury discretion** distributed via buyback-and-distribute."

#### The 7-8% gap

```mermaid
flowchart TB
    CLAIM["MARKETING SITE<br/>ftUSD generates 7-8% APY<br/>delta-neutral, perfect 1 dollar peg"]

    REAL["DOCS STAGE 0 - WHAT IS LIVE<br/>ftUSD is a USDC/USDT to Aave wrapper<br/>the only implemented strategy"]

    BENCH["DOCS OWN BENCHMARK TABLE<br/>Aave USDC 3.50% / Compound USDC 3.52%<br/>Aave USDT 2.56% / Lido stETH 2.55%"]

    CLAIM --> GAP{"Gap<br/>7-8% claimed<br/>vs 2.55-3.52% available"}
    BENCH --> GAP
    REAL --> GAP

    GAP --> Q{"What fills the gap?"}

    Q -->|"Option 1"| LEV["Loop collateral prudently<br/>deposit stS back to money market<br/>roughly 2.5x looping"]
    Q -->|"Option 2"| FWD["A forward-looking target<br/>delta-neutral is Stage 3+<br/>not deployed"]

    LEV --> C1["CONTRADICTION<br/>Looping is leverage<br/>backing mandate says no leverage"]
    FWD --> C2["CONTRADICTION<br/>Marketed in present tense<br/>as a live APY"]

    classDef claim fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class CLAIM claim
    class REAL,BENCH,GAP,Q neutral
    class LEV,FWD warn
    class C1,C2 bad
```

#### What the "yield" is actually paid in

```mermaid
flowchart LR
    Y["Net strategy yield<br/>and protocol fee revenue"]

    Y --> T["Protocol treasury"]
    T --> D{"At TREASURY DISCRETION<br/>distribute via<br/>buyback-and-distribute"}

    D -->|"staked ftUSD only"| FT["Rewards paid in FT<br/>claimed from rewards vault<br/>no auto-compounding"]
    D -->|"unstaked ftUSD"| NONE["Receives NO yield<br/>proceeds accrue to<br/>the protocol treasury"]

    FT --> MKT["To realise USD you must sell FT<br/>into a 2.1M float<br/>on 265K/day of volume"]
    MKT --> PRICE["The same party sets the buyback bid<br/>and the reward rate"]

    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class Y,T,D,NONE neutral
    class FT warn
    class MKT,PRICE bad
```

Realised USD return = (FT received) x (price you can exit at). Both legs are controlled by
the same party. That is a discretionary token distribution, not a yield.

## 5. What is actually open source

| Repo | Contents |
|---|---|
| `flyingtulipdotcom/ft` | **Only the FT ERC20/OFT token** (~370 LoC Solidity) + deploy scripts |
| `flyingtulipdotcom/escrow` | ~50-line "trusted token transfer" escrow |
| `flyingtulipdotcom/security` | `KNOWN_ISSUES.md` + Sherlock bounty pointer |
| `flyingtulipdotcom/supporter-whitelist` | Yearn/Keep3r/Fantom/Sonic supporter list |

```mermaid
flowchart TB
    subgraph PUB["PUBLISHED - 4 repos, ~420 LoC of Solidity"]
        direction LR
        R1["ft<br/>FT.sol token only"]
        R2["escrow<br/>50-line escrow"]
        R3["security<br/>KNOWN_ISSUES.md + bounty"]
        R4["supporter-whitelist<br/>CSV of supporters"]
    end

    subgraph PRIV["NEVER PUBLISHED - named in KNOWN_ISSUES.md"]
        direction LR
        P1["PutManager<br/>holds 100% of backing capital"]
        P2["AaveStrategy"]
        P3["YieldClaimer"]
        P4["LeverageRfqEngine"]
        P5["CircuitBreaker<br/>ftDNMM"]
        P6["pFTMarketplace"]
        P7["PositionsManager"]
    end

    COV["Public coverage of the closed half:<br/>Sherlock bug bounty only<br/>no published audit report"]

    PUB -->|"documents risks in"| PRIV
    PRIV --> COV

    style PUB fill:#dcfce7,stroke:#16a34a,color:#14532d
    style PRIV fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    class COV warn
```

**Read this as a coverage statement, not a criticism of intent.** Publishing
`KNOWN_ISSUES.md` naming your own residual risks is better practice than most. But the
third-party-audited surface is a **50-line helper contract**, while the contract
custodies all user collateral is unreviewed by the public.

**The protocol itself is closed-source.** The `KNOWN_ISSUES.md` names the real system:
`PutManager`, `AaveStrategy`, `YieldClaimer`, `LeverageRfqEngine`, `CircuitBreaker`
(ftDNMM), `pFTMarketplace`, `PositionsManager`, plus strategy-management roles and
timelocks. **None of that code is public.** The contract that custodies 100% of the
backing capital — `PutManager` — cannot be reviewed by the public; it is covered only
by a Sherlock bug bounty.

Bug bounty: https://audits.sherlock.xyz/bug-bounties/248
