# Weaknesses in the "High Yield" Reasoning

This is the economic critique. It does **not** claim Flying Tulip is a scam or is
insolvent. It argues that the *reasoning used to justify a high yield* does not survive
contact with the protocol's own numbers.

---

## The identity that breaks the pitch

The docs make two claims that cannot both be load-bearing:

> **Claim A:** "Backing capital is **never spent**." It sits in "safe, liquid,
> **low-risk, no-leverage**, no-bridging" positions so Exit-at-par can be honoured
> "quickly in all conditions."

> **Claim B:** Holders earn attractive returns, funded by buyback-and-burn from
> "surplus backing capital yield" — and ftUSD is marketed at **7-8% APY**.

If Claim A is true, then the only cash flow the system can generate is **the native
yield on a safe, unlevered, liquid portfolio**. That yield is bounded, and the docs
publish the bound themselves:

| Benchmark (docs' own table, Ethereum) | APY |
|---|---|
| Aave v3 USDC supply | **3.50%** |
| Compound v3 USDC supply | **3.52%** |
| Aave v3 USDT supply | **2.56%** |
| Lido stETH staking | **2.55%** |

> **Yield-to-holder ≤ (yield on collateral) − (operating costs).**

You cannot pay 7-8% out of a portfolio earning ~3% while preserving principal, unless
the gap is filled by **new capital**. That is the whole argument. Everything below is a
consequence of it.

```mermaid
flowchart TB
    A["CLAIM A - the safety claim<br/>Backing capital is NEVER SPENT<br/>safe, liquid, low-risk, NO-LEVERAGE<br/>so Exit-at-par is honoured<br/>quickly in all conditions"]

    B["CLAIM B - the return claim<br/>Holders earn attractive yield from<br/>surplus backing capital yield<br/>ftUSD marketed at 7-8% APY"]

    A --> CONS["What A actually constrains<br/>the ONLY cash flow available is the<br/>NATIVE YIELD on a safe,<br/>unlevered, liquid portfolio"]

    CONS --> BOUND["And the docs publish the bound themselves<br/>Aave v3 USDC 3.50%<br/>Compound v3 USDC 3.52%<br/>Aave v3 USDT 2.56%<br/>Lido stETH 2.55%"]

    BOUND --> IDENT["THE IDENTITY<br/>yield to holder<br/>is less than or equal to<br/>yield on collateral MINUS operating costs"]

    B --> TEST{"Can 7-8% survive<br/>that identity?"}
    IDENT --> TEST

    TEST -->|"NO"| GAP["The gap must be filled by one of:<br/>1. new capital<br/>2. other holders' principal<br/>3. a token price the issuer's own<br/>buyback sets in a 2.1M float"]

    TEST -->|"the only way out"| ESCAPE["Break Claim A<br/>take leverage or risk<br/>which the mandate forbids"]

    classDef claim fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class A,B claim
    class CONS,BOUND,TEST neutral
    class IDENT good
    class GAP,ESCAPE bad
```

---

## W-01 — "Principal protection" and "unlimited upside" are mutually exclusive

The Perpetual PUT offers three choices, but you can only ever *use* one per unit of FT:

| Choice | Outcome |
|---|---|
| **Exit at par** | Exactly your principal back. **0% nominal return.** |
| **Withdraw** | You get tradeable FT — but the PUT is **"invalidated forever"** on that portion. |

```mermaid
flowchart TD
    PITCH["MARKETED PACKAGE<br/>100% downside protection<br/>PLUS unlimited upside"]

    PITCH --> REALITY["ACTUAL STRUCTURE<br/>a BINARY and IRREVERSIBLE choice<br/>protection OR upside, never both"]

    REALITY --> EX["Exit at par"]
    REALITY --> WD["Withdraw"]

    EX --> EXR["Exactly your principal back<br/>NOMINAL RETURN 0%<br/>PUT consumed"]
    WD --> WDR["Tradeable FT<br/>PUT invalidated FOREVER"]

    EXR --> MARG["So the marginal holder<br/>decides purely on price"]
    WDR --> MARG

    MARG --> UP{"Is FT above par?"}
    UP -->|"yes"| CW["WITHDRAW<br/>capture the upside<br/>FORFEIT the protection"]
    UP -->|"at or below par"| CE["EXIT AT PAR or hold<br/>keep the protection<br/>FORFEIT the upside"]

    CW --> CONC["CONSEQUENCE<br/>protection is only ever claimed by people<br/>who are giving up the upside, and upside<br/>only by people who have given up the<br/>protection - the two legs never coexist<br/>in the same hands when either matters"]
    CE --> CONC

    classDef claim fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class PITCH claim
    class REALITY,EX,WD,MARG,UP neutral
    class EXR,WDR warn
    class CW,CE,CONC bad
```

So the "100% downside protection + unlimited upside" package is not a package. It is a
**binary, irreversible choice**: protection *or* upside, never both simultaneously, and
once you take the upside the protection is gone permanently.

That is not a criticism by itself — it is the payoff of any put-plus-call structure. The
problem is that it is marketed as both at once, and the *marginal* holder will rationally
choose as follows:

- FT **above** par → Withdraw (capture upside, forfeit protection)
- FT **at or below** par → Exit at par (or hold and wait)

Which means **the protection is only ever claimed by people who are giving up the
upside, and the upside is only ever claimed by people who have given up the
protection.** The two legs never coexist in the same hands at the moment they matter.

---

## W-02 — The buyback is funded mainly by principal, not by yield

Three funding sources are listed. Only one is actually yield:

| Source | Is it yield? |
|---|---|
| **A.** Surplus backing-capital yield | ✅ Yes — but it is the *residual after opex* |
| **B.** Protocol revenue & fees | ⚠️ Real, but currently trivial |
| **C.** Released backing capital from **Withdrawals** | ❌ **No — this is someone's principal** |

Source **C** is the one that actually scales. When a holder Withdraws, the backing
capital reserved for their Exit is spent buying and burning FT. That is a **transfer
from the withdrawer to the remaining holders**, not value creation.

### The reflexivity loop

```
FT trades above par
  → Withdraw looks attractive
  → backing capital released
  → protocol market-buys FT (the only structural bid)
  → price rises
  → Withdraw looks more attractive
  → more backing released  ⟲
```

```mermaid
flowchart TB
    P1["FT trades above par"]
    P1 --> P2["Withdraw looks attractive"]
    P2 --> P3["Holder Withdraws<br/>PUT invalidated forever"]
    P3 --> P4["Backing capital reserved for<br/>their Exit is RELEASED"]
    P4 --> P5["Protocol market-buys FT<br/>the ONLY structural bid"]
    P5 --> P6["FT price rises"]
    P6 -->|"feedback"| P2

    P4 --> SRC{"Is this yield?"}
    SRC -->|"NO"| PRIN["It is the withdrawer's PRINCIPAL<br/>a transfer from leavers<br/>to remaining holders"]
    SRC -->|"YES"| YLD["Only source A qualifies<br/>and it is a residual after opex"]

    PRIN --> ONCE["So the buyback yield is a<br/>ONE-TIME transfer per withdrawing holder<br/>NOT a recurring return"]

    P5 --> BID["The buyback IS the market<br/>in a 2.1M float on 265K/day"]

    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class P1,P2,P3,P4,P5,P6,SRC neutral
    class PRIN,ONCE,BID bad
    class YLD good
```

#### The float maths

```mermaid
flowchart LR
    S1["Holder withdraws 10,000 FT<br/>1,000 dollars of backing released"]
    S1 --> S2["Protocol buys at 0.15<br/>retires 6,667 FT"]
    S2 --> S3["Holder sold 10,000 FT<br/>into the market"]
    S3 --> S4["NET FLOAT CHANGE<br/>+3,333 FT"]

    S4 --> S5["Each withdrawal INCREASES float<br/>while REMOVING collateral"]

    S5 --> GOOD["In fairness<br/>backing per remaining PUT holder<br/>stays at exactly 0.10<br/>so the loop is NOT dilutive"]

    S5 --> BAD["But the mechanism sold as<br/>creating scarcity is in aggregate<br/>ADDING to the float"]

    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class S1,S2,S3,S4 neutral
    class S5,BAD bad
    class GOOD good
```

This loop **consumes the collateral base**. Every pass converts hard backing capital
into burned FT. The burn is real, but it is paid for by shrinking the assets.

Run to completion: backing → 0, supply falls, float rises, and what remains is an
uncollateralised float token. Nobody is insolvent along the way (the 1:1 coverage holds
throughout), but **the "buyback yield" is a one-time transfer per withdrawing holder,
not a recurring return.**

### The float maths

Backing per remaining PUT holder stays at exactly $0.10 through the loop, so the loop is
**not** dilutive — credit where due. But note what happens to float:

- Holder withdraws 10,000 FT; $1,000 backing released.
- Protocol buys at $0.15 → retires 6,667 FT.
- Holder sold 10,000 FT into the market.
- **Net float change: +3,333 FT.**

Each withdrawal **increases** float. Buybacks offset only part of it. So the mechanism
that is supposed to create scarcity is, in aggregate, adding to the float while removing
collateral.

---

## W-03 — The float is far too small for the mechanism to be real

Verified on-chain (2026-09-02):

| Metric | Value |
|---|---|
| Price | $0.1014 |
| Float (`availableSupply`) | **20,668,218 FT** |
| **Float market cap** | **≈ $2.10M** |
| FDV (1.199B × price) | **≈ $121.6M** |
| 24h volume | **$264,564** |
| Holders | **688** |

The docs' worked example has a holder withdrawing 10,000 FT and selling at $0.15. That is
$1,500 — fine. But:

- The buyback must buy into a **$2.1M float with $265K/day of volume**. Any
  non-trivial buyback *is* the market.
- Therefore the FT price — the thing that sets the "unlimited upside" for the
  1.199B locked FT — is set by the issuer's own bid in a market that cannot absorb the
  exits it advertises.
- The paper value of PUT holders' upside is a mark on an illiquid float. **It is not
  realisable at scale.**

And the reverse: a $2M float with $265K daily volume is trivially manipulable in *both*
directions by anyone, not just the protocol.

---

## W-04 — The yield is junior to the team's operating budget

> "The **first call** on the backing capital yield is to fund the ongoing development of
> the ecosystem, infrastructure and operations."
> "Any **remaining** backing capital yield after the ecosystem budget is met is used for
> continuous buyback-and-burn."

Backing capital ≈ $120M (implied by 1.199B FT at 10 FT/$1).

```
Gross carry @ 3.5%          ≈  $4.2M / yr
Less ecosystem budget       ≈ -$4.0M / yr   (salaries, marketing, infra, ops)
─────────────────────────────────────────
Surplus available to burn   ≈  $0.2M / yr
```

```mermaid
flowchart TB
    BC["Backing capital approx 120M<br/>implied by 1.199B FT at 10 FT per dollar"]

    BC --> GROSS["GROSS CARRY at 3.5%<br/>approx 4.2M per year"]

    GROSS --> W1["FIRST CALL: ecosystem budget<br/>salaries, marketing, infra, ops<br/>approx minus 4.0M per year"]

    W1 --> SURPLUS["SURPLUS available to burn<br/>approx 0.2M per year"]

    SURPLUS --> PCT["0.16% of the 121.6M FDV<br/>PER YEAR"]

    W1 --> ZERO["If the budget absorbs all the yield<br/>there is NO surplus<br/>no buyback from this source"]

    ZERO --> QUOTE["The docs concede this themselves:<br/>if the ecosystem budget consumes all<br/>the yield, there is no surplus"]

    PCT --> ALT["Realistic holder yield is approx ZERO<br/>and the buyback then depends on revenue<br/>from a protocol with 265K daily volume<br/>and 688 holders"]

    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class BC,GROSS neutral
    class W1,SURPLUS warn
    class PCT,ZERO,QUOTE,ALT bad
```

$0.2M/yr against a $121.6M FDV is **0.16% per year**. That is the entire yield if the
ecosystem budget absorbs the carry — which, for a team of this profile, it plausibly
does. The docs concede the point: *"if the ecosystem budget consumes all the yield,
there is no surplus → no buyback from this source."*

So in the realistic case, holder yield ≈ **0**, and the buyback depends on protocol
revenue from a protocol with **$265K of daily volume and 688 holders**.

---

## W-05 — The 7-8% ftUSD APY is not supported by the deployed product

| | |
|---|---|
| **Marketing site** | ftUSD "generates **7-8% APY** through delta-neutral strategies while maintaining a perfect $1 peg" |
| **Docs, actual Stage 0** | "At launch, ftUSD is a **USDC/USDT to Aave wrapper**." **Only implemented strategy.** |
| **Docs, delta-neutral** | **Stage 3+** — roadmap, not deployed |
| **Docs, benchmark rates** | Aave USDC **3.50%**, Aave USDT **2.56%**, Compound USDC **3.52%**, Lido stETH **2.55%** |
| **Docs, "7-8%"** | **The figure does not appear anywhere in the documentation.** |

To get from ~3% to 7-8% you need roughly 2.5x looping. The docs describe exactly that:

> "**Loop collateral prudently** (e.g. deposit stS back to the money market) to increase
> safety buffers and **carry**."

```mermaid
flowchart TB
    S0["STAGE 0 - WHAT IS LIVE<br/>ftUSD is a USDC/USDT to Aave wrapper<br/>the only implemented strategy<br/>yields approx 3.5%"]

    NEED["MARKETED TARGET<br/>7-8% APY"]

    S0 --> GAP["Gap to close: roughly 2x to 2.5x<br/>the available carry"]
    NEED --> GAP

    GAP --> L1["Loop 1<br/>supply USDC, borrow S, stake to stS"]
    L1 --> L2["Loop 2<br/>deposit stS back to the money market<br/>to increase safety buffers AND carry"]
    L2 --> L3["Each loop adds carry<br/>and also adds leverage,<br/>liquidation risk and funding risk"]

    L3 --> CONTRA["CONTRADICTION<br/>the backing capital mandate says<br/>safe, liquid, low-risk, NO-LEVERAGE"]

    NEED --> STAGE3["Delta-neutral is STAGE 3+<br/>a roadmap item, not deployed"]

    STAGE3 --> CONTRA2["The 7-8% is either<br/>a forward-looking target<br/>or it requires leverage<br/>either way it is not live today"]

    classDef claim fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class NEED claim
    class S0,GAP,L1,L2,L3,STAGE3 neutral
    class CONTRA,CONTRA2 bad
```

**Looping is leverage.** The backing-capital mandate says "no leverage." Either the
7-8% requires leverage (contradicting the safety claim), or it is a forward-looking
number for a strategy that does not exist yet.

### And the yield is paid in FT, at treasury discretion

> "Stakers claim rewards as **FT** from the rewards vault."
> "All net strategy yield and protocol fee revenue is collected by the protocol
> treasury; then **at treasury discretion** distributed via buyback-and-distribute."
> "Unstaked ftUSD receives no yield; proceeds accrue to the **protocol treasury**."

So the "7-8% stablecoin yield" is:

1. Paid **in the protocol's own token**, not in USD;
2. Bought back **at the treasury's discretion**;
3. In a market with **$265K/day** of volume.

Your realised USD return = (FT received) × (price you can exit at). **Both legs are
controlled by the same party.** This is not a yield; it is a discretionary token
distribution priced by the issuer's own bid.

---

## W-06 — "No leverage, low risk" is not true of the stated venues

The backing venues are listed as "safe, liquid, low-risk, **no-leverage**". Two problems:

**(a) sUSDe is leverage that lives off-chain.** sUSDe (Ethena) *is* a delta-neutral basis
trade — perp funding plus staking, held at exchanges and custodians. It carries funding-rate
risk, exchange risk, and custody risk. Classifying it under "no leverage" is true only if
you define leverage as "on-chain borrow." The economic exposure is levered.

**(b) The LSTs have exit queues.** stETH, jupSOL, and AVAX staking all involve unbonding.
The docs admit it:

> "In synchronized **Exit** waves, some positions (e.g. **LST withdrawals**) can
> introduce timing delays."
> "Some backing capital positions (e.g. stETH, jupSOL, AVAX) may require **exit queues**
> or unbonding."

### This is the deepest structural flaw: liquidity transformation

| Liabilities | Assets |
|---|---|
| Perpetual PUT: **instant, perpetual, unconditional, evergreen** | stETH / jupSOL / AVAX: **queued, unbonding** |

```mermaid
flowchart TB
    subgraph LIAB["LIABILITIES - the Perpetual PUT"]
        direction LR
        L1["INSTANT"]
        L2["PERPETUAL"]
        L3["UNCONDITIONAL"]
        L4["EVERGREEN"]
    end

    subgraph ASSET["ASSETS - stated backing venues"]
        direction LR
        A1["stETH<br/>exit queue"]
        A2["jupSOL<br/>exit queue"]
        A3["AVAX staking<br/>unbonding"]
        A4["sUSDe<br/>off-chain basis trade"]
        A5["Aave stables<br/>the only liquid leg"]
    end

    LIAB --> MISMATCH["LIQUIDITY TRANSFORMATION<br/>on-demand liabilities funded with<br/>queued, unbonding assets"]
    ASSET --> MISMATCH

    MISMATCH --> DOC["The docs admit it<br/>synchronized Exit waves can introduce<br/>timing delays; some positions may require<br/>exit queues or unbonding"]

    DOC --> SIZING["Offered mitigation<br/>exposures are sized for timely unwinds"]

    SIZING --> FLAW["Sizing for EXPECTED redemptions is<br/>precisely the bank-run failure mode<br/>the protection is weakest exactly<br/>when it is needed"]

    FLAW --> VERDICT["An American put that cannot be settled<br/>on demand is not an American put"]

    style LIAB fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    style ASSET fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class MISMATCH,DOC,SIZING neutral
    class FLAW,VERDICT bad
```

The docs say exposures are "sized for timely unwinds." Sizing for *expected* redemptions
is precisely the failure mode of every bank run: **the protection is most likely to be
stressed exactly when it is needed, and it weakest at that moment.**

An American put that cannot be settled on demand is not an American put. "100% capital
protection" and "may require exit queues" cannot both be true claims.

---

## W-07 — The 40:40:20 rule creates a self-served accounting conflict

> "**Revenue-funded** buybacks unlock Foundation / Team / Incentives **1:1** (40:40:20)."
> "Buyback-and-burn funded **only by backing capital yield does not unlock anything**."

So the team unlocks tokens **only** when a burn is classified as revenue-funded. The
team therefore has a **direct financial incentive to classify every buyback as
"revenue-funded"** rather than "yield-funded."

Nothing in the docs:
- defines the boundary between the two sources,
- discloses the **size** of the Foundation / Team / Incentives allocations, or
- constrains the treasury's discretion over the split.

```mermaid
flowchart TD
    BURN["A buyback-and-burn happens"]

    BURN --> CLASS{"How is it CLASSIFIED?"}

    CLASS -->|"revenue-funded"| UNLOCK["Foundation / Team / Incentives<br/>unlock 1:1 at 40:40:20"]
    CLASS -->|"backing capital yield only"| NOUNLOCK["Unlocks NOTHING<br/>supply merely shrinks"]

    UNLOCK --> INCENT["The team unlocks ONLY when a burn is<br/>classified as revenue-funded<br/>so the team has a DIRECT FINANCIAL<br/>INCENTIVE to classify every buyback<br/>as revenue-funded"]

    INCENT --> NODEF["Nothing in the docs:<br/>1. DEFINES the boundary between the two sources<br/>2. DISCLOSES the size of Foundation / Team / Incentives<br/>3. CONSTRAINS treasury discretion over the split"]

    NODEF --> GOODPART["The IDEA is genuinely good<br/>tying insider vesting to value actually<br/>returned to holders beats time-based vesting"]

    NODEF --> BADPART["The IMPLEMENTATION gives the beneficiary<br/>unilateral discretion over the classification<br/>that triggers their own unlock"]

    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class BURN,CLASS neutral
    class UNLOCK,INCENT,NODEF warn
    class NOUNLOCK,BADPART bad
    class GOODPART good
```

The *idea* — tie insider vesting to value actually returned to holders — is genuinely
good, and better than time-based vesting. The *implementation* gives the beneficiary
unilateral discretion over the classification that triggers their own unlock.

---

## W-08 — The supply disclosure gap invalidates the published FDV maths

The docs say: **10,000,000,000 FT**, "minted at deployment," "no additional minting,"
"totalSupply stays at 10B."

On-chain across all five EVM deployments: **1,198,639,737 FT** — a gap of ~8.8B (88%).

At the stated 10 FT/$1 rate, 1.199B FT implies **≈ $119.9M committed**, which is *below*
the claimed **$200M private round** on its own.

```mermaid
flowchart TB
    DOC["DOCS<br/>10,000,000,000 FT<br/>minted at deployment<br/>no additional minting<br/>totalSupply stays at 10B"]

    CHAIN["CHAIN<br/>1,198,639,737 FT<br/>summed across 5 EVM deployments"]

    DOC --> GAP["GAP approx 8.8B FT = 88% of stated supply"]
    CHAIN --> GAP

    GAP --> RATE["At the stated 10 FT per dollar<br/>1.199B FT implies approx 119.9M committed"]
    RATE --> CLAIM["Press and docs claim<br/>a 200M private round"]
    CLAIM --> DISC["119.9M is BELOW the claimed round<br/>on its own"]

    GAP --> MODEL["Anyone modelling the docs' worked example<br/>500m committed gives 5B FT allocated<br/>and 5B FT non-circulating<br/>is modelling a supply that DOES NOT EXIST"]

    GAP --> CAV["CAVEAT - stated honestly<br/>mint/burn history not fully reconstructed<br/>eth_getLogs capped at 50k blocks, no explorer key<br/>the 8.8B may have been burned in an<br/>event I could not page through<br/>either way it is UNDISCLOSED"]

    classDef claim fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class DOC,CLAIM claim
    class CHAIN,RATE neutral
    class GAP,DISC,MODEL bad
    class CAV warn
```

Anyone modelling the docs' worked example — *"$500m committed → 5B FT allocated, 5B FT
remain non-circulating"* — is modelling a supply that does not exist. (I could not fully
reconstruct mint/burn history: public RPCs cap `eth_getLogs` at 50k blocks and I had no
explorer API key. The 8.8B may have been burned in an event I could not page through.
Either way it is undisclosed.)

---

## W-09 — "Oracle-free" removes manipulation resistance, not manipulation incentive

Futures are marketed as "oracle-free," and ftUSD as having "no oracles or centralized
systems." These are framed as safety features.

But delta-neutral hedging requires a **reliable mark** on the basis. If the mark comes
from the protocol's own AMM — a pool with a **$2.1M float** — then:

- the hedge is marked against a price the protocol itself moves through buybacks, and
- the price is cheap to push for anyone with size.

Removing the external oracle removes the *independent reference*, which is the thing
that makes manipulation expensive. It does not remove the incentive to manipulate; it
reduces the cost of doing so.

---

```mermaid
flowchart TB
    CLAIM["MARKETED AS A SAFETY FEATURE<br/>Futures are oracle-free<br/>ftUSD has no oracles or centralized systems"]

    CLAIM --> BENEFIT["Genuine benefit<br/>removes oracle manipulation and<br/>oracle downtime as attack surfaces"]

    CLAIM --> NEED["But delta-neutral hedging<br/>REQUIRES a reliable mark on the basis"]

    NEED --> SRC{"Where does the mark come from?"}

    SRC -->|"the protocol's own AMM"| POOL["A pool with a 2.1M float"]

    POOL --> C1["The hedge is marked against a price<br/>the protocol itself moves through buybacks"]
    POOL --> C2["The price is cheap to push<br/>for anyone with size"]

    C1 --> VERDICT["Removing the external oracle removes the<br/>INDEPENDENT REFERENCE - which is the thing<br/>that makes manipulation expensive"]
    C2 --> VERDICT

    VERDICT --> FINAL["It does NOT remove the incentive to manipulate<br/>it REDUCES THE COST of doing so"]

    classDef claim fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class CLAIM claim
    class NEED,SRC,POOL neutral
    class BENEFIT good
    class C1,C2,VERDICT,FINAL bad
```

## What is genuinely good

Being fair matters here, because the structure is more honest than most:

- **1:1 backing that is actually ring-fenced is a real improvement** over the
  emission-funded "yield" that dominates DeFi. If they honour it, par exits are
  substantially safer than the typical farm.
- **No inflation** is a real constraint, voluntarily accepted.
- **Revenue-linked insider unlocks** are a better alignment mechanism than time vesting,
  even with the classification problem in W-07.
- **The perpetual put is a genuinely novel retail-protective idea**, and putting it
  on-chain rather than in a term sheet is a real contribution.
- **Publishing `KNOWN_ISSUES.md`** with candid residual-risk admissions
  (PM-02 "protocol-level losses are not handled on-chain", CB-01, MKT-01) is better
  practice than most projects at this stage.

---

## The one-sentence version

> **If the principal is genuinely never spent and genuinely unlevered, the yield is
> capped at the ~3% the collateral earns — so any yield materially above that is being
> paid out of new capital, out of other holders' principal, or out of a token price that
> the issuer's own buyback sets in a $2M float.**
