# Findings — `contracts/FT.sol`

Source: `github.com/flyingtulipdotcom/ft`, `contracts/FT.sol` (370 LoC, solc ^0.8.30,
ERC20 + LayerZero OFT + ERC20Permit + Pausable + Ownable).

> Framing note. `FT.sol` is a small, competently written token. I found **no
> arithmetic bug, no reentrancy, and no signature-replay flaw** — I verified the two
> hardcoded EIP-712 typehashes against independently computed keccak values and both
> match. The material issues below are **privilege and pause-semantics** issues, which
> is the right thing to focus on for a token whose entire supply was premined to a
> single role.

---

## FT-01 — The pause is a one-directional freeze: the configurator keeps full transfer ability

**Severity: High (centralisation) · Status: partially acknowledged upstream as "Low" (their Q-2)**

`_update` (L346–369):

```solidity
if (!paused()) { super._update(from, to, value); return; }

address ftConfigurator = _configurator;
if (from == ftConfigurator || to == ftConfigurator) {   // L357  <-- exempt
    super._update(from, to, value); return;
}

address sender = _msgSender();
if (sender == address(endpoint) || sender == ftConfigurator) {  // L363 <-- exempt
    super._update(from, to, value); return;
}

revert EnforcedPause();
```

### What `_update` actually does when paused

```mermaid
flowchart TD
    START["FT._update called<br/>transfer / transferFrom / mint / burn"]

    START --> Q1{"paused?"}
    Q1 -->|"no"| OK1["super._update<br/>transfer proceeds for everyone"]

    Q1 -->|"yes"| Q2{"from == configurator<br/>OR to == configurator?<br/>L357"}
    Q2 -->|"yes"| OK2["BYPASS<br/>transfer proceeds"]

    Q2 -->|"no"| Q3{"msg.sender == endpoint<br/>OR msg.sender == configurator?<br/>L363"}
    Q3 -->|"yes"| OK3["BYPASS<br/>transferFrom any A to any B<br/>subject only to A's allowance"]

    Q3 -->|"no"| REV["revert EnforcedPause()<br/>every ordinary holder frozen"]

    OK2 --> C1["Configurator can SEND to anyone"]
    OK2 --> C2["Anyone can SEND to the configurator"]
    OK3 --> C3["Configurator can move<br/>THIRD-PARTY balances"]

    REV --> C4["Ordinary holders cannot transfer"]
    C4 --> C5["Users cannot even BURN<br/>see FT-04"]

    C1 --> VERDICT["setPaused(true) is not a freeze<br/>it is a selective denial of service<br/>against everyone except the insider"]
    C2 --> VERDICT
    C3 --> VERDICT
    C5 --> VERDICT

    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class START,Q1,Q2,Q3 neutral
    class OK1 good
    class OK2,OK3,C1,C2,C3 warn
    class REV,C4,C5,VERDICT bad
```

The `endpoint` exemption at L363 is **correct and necessary** — LayerZero V2 needs it for
OFT credit/debit, and I checked it. The problem is specifically the two `configurator`
branches sitting alongside it.

While paused, **every** ordinary holder reverts. The configurator does not:

- It can send FT to anyone (`from == configurator`).
- Anyone can send FT to it (`to == configurator`).
- As `msg.sender`, it can call `transferFrom(A, B, v)` for **any** A and B, subject only
  to A having granted it an allowance.

So `setPaused(true)` is not a freeze — it is a **selective denial of service against
everyone except the insider**. The insider retains a fully functioning token while the
float is immobilised. This matters here more than in a typical token because:

1. The configurator Safe **holds 54% of supply** (648M FT, verified on-chain).
2. The configurator is *also* the LayerZero `delegate` — the same key across all five
   chains (`utils/constants.ts`).
3. The configurator Safe shares **4 of 5 signers** with the `owner` Safe, so the pause
   power and the pause-exemption are not independently controlled.

**Upstream downgrades this to "Low / intentional for recovery workflows."** I think that
is the wrong rating for a token sold to the public on a "100% capital protection"
promise: the recovery carve-out is broad enough to move third-party balances, not just
to recover the protocol's own funds.

**Recommendation.** Narrow the exemption to `from == configurator` (protocol-owned
funds) and drop the open-ended `msg.sender == configurator` branch, or gate it behind a
separate, timelocked `emergencyRecovery` flag with an event and a bounded scope.

---

## FT-02 — Entire 10B supply premined to the configurator, contract deployed paused

**Severity: Medium · Status: by design, but worth stating plainly**

```solidity
if (block.chainid == mintChainId) {
    _mint(ftConfigurator, 10_000_000_000e18);   // L85
}
_pause();                                        // L87
```

Genesis state: one role owns 100% of supply, and all transfers are disabled. The token
only becomes usable when that role unpauses and distributes. Combined with FT-01, the
launch configuration is **complete insider control**; there is no moment at which
 holders have a claim the configurator cannot unilaterally override.

This is normal for a token launch, but "10B premined to a 3-of-4 Safe, deployed paused,
pause is asymmetric" is the honest description of the trust model, and it is not the
impression created by "no vesting, no lockup, no inflation, 100% capital protection."

---

## FT-03 — `setName` / `setSymbol` mutate the EIP-712 domain separator and the token's identity, with no timelock

**Severity: Medium · Status: upstream rates this Informational (their I-3)**

```solidity
function setName(string memory newName) external onlyOwner { _setName(newName); }   // L169
function _domainSeparatorDynamic() internal view returns (bytes32) { ... keccak256(bytes(name())) ... }  // L209
```

Two distinct problems:

**(a) Cross-chain domain-separator desynchronisation.** `name()` is per-chain state fed
into the domain separator. FT is an OFT deployed on five chains. Renaming on one chain
and not the others leaves the chains with different separators, so a permit valid on
chain A is invalid on chain B, and integrators' cached separators are stale *by
different amounts* on each chain. Because `DOMAIN_SEPARATOR()` is recomputed on every
call, there is no on-chain signal that a rotation happened; integrators can only detect
it by polling.

**(b) Identity spoofing.** The owner can rename FT to `"USD Coin"` / `"USDC"`. Any
wallet, aggregator, or frontend that renders `name()`/`symbol()` will display it. This
is a cheap, high-leverage phishing primitive and there is no bound on string length, so
`name()` can also be made enormous to gas-grief consumers.

```mermaid
flowchart TB
    CALL["owner calls setName on Chain A<br/>no timelock"]

    CALL --> DS["DOMAIN_SEPARATOR is recomputed<br/>on EVERY call from name()<br/>L209: keccak256 of bytes of name"]

    DS --> CH["FT is an OFT on 5 chains<br/>name() is PER-CHAIN state"]

    CH --> A["Chain A<br/>renamed<br/>NEW separator"]
    CH --> B["Chain B<br/>not renamed<br/>OLD separator"]
    CH --> C["Chain C, D, E<br/>not renamed<br/>OLD separator"]

    A --> P1["A permit signed against the<br/>new separator is INVALID on B-E"]
    B --> P2["Integrators cached separators<br/>are stale by DIFFERENT amounts<br/>on each chain"]

    DS --> SIG["No on-chain signal that a<br/>rotation happened - the event<br/>only carries the NEW value"]
    SIG --> P3["Integrators can only detect it<br/>by polling every chain"]

    CALL --> SPOOF["Identity spoofing<br/>owner can setName to 'USD Coin'<br/>and setSymbol to 'USDC'"]
    SPOOF --> S1["Wallets, aggregators and frontends<br/>render name() and symbol() verbatim"]
    CALL --> LEN["No bound on string length"]
    LEN --> L2["name() can be made enormous<br/>to gas-grief consumers"]

    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class CALL,DS,CH,SIG,LEN neutral
    class A,B,C warn
    class P1,P2,P3 bad
    class SPOOF,S1,L2 bad
```

**Recommendation.** Timelock renames, emit the old and new value in the event (currently
the event only carries the new value), cap string length, and treat a rename as a
coordinated multi-chain operation.

---

## FT-04 — Users cannot burn while paused; the configurator can

**Severity: Low**

`burn()` / `burnFrom()` route through `_update(from, address(0), v)`. While paused,
`from` is the user (not the configurator) and `to` is `address(0)` (not the
configurator), and `msg.sender` is the user → `revert EnforcedPause()`. The configurator
is exempt. There is no stated reason a user should be prevented from *destroying* their
own tokens during a freeze, and it removes the only action a holder might use to exit a
compromised position.

---

## FT-05 — Two `permit` entrypoints share one nonce space

**Severity: Low · ( partly inherent to ERC-2612 )**

`permit(..., uint8 v, bytes32 r, bytes32 s)` (L221) and the ERC-1271
`permit(..., bytes signature)` (L292) both read and consume `nonces(owner)`. Any third
party can front-run *either* overload to consume the victim's current nonce and revert
their transaction. This griefing is permanent for that nonce. Standard permit
front-running applies, but the second overload doubles the observable surface for
mempoel watchers.

The ERC-1271 branch (L310–315) calls `isValidSignature` **before** consuming the nonce,
so a reentrant owner contract recurses; this self-limits by gas exhaustion and reverts,
so it is not exploitable, but it is fragile-by-accident rather than by design.

```mermaid
flowchart TB
    N["nonces owner<br/>ONE shared counter"]

    N --> P1["permit ECDSA overload L221<br/>v, r, s"]
    N --> P2["permit ERC-1271 overload L292<br/>bytes signature"]

    P1 --> SHARED["Both read and consume<br/>the SAME nonce space"]
    P2 --> SHARED

    SHARED --> FR{"Either overload can be<br/>front-run to consume<br/>the victim's current nonce"}
    FR --> REV["Victim transaction reverts<br/>griefing is PERMANENT for that nonce"]

    P2 --> ORDER["L310-315 calls isValidSignature<br/>BEFORE consuming the nonce"]
    ORDER --> REENT["A reentrant owner contract recurses"]
    REENT --> BOUND["Self-limits by gas exhaustion and reverts<br/>NOT exploitable today"]

    BOUND --> FRAG["But this is fragile by ACCIDENT<br/>not by design"]

    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class N,P1,P2,SHARED,FR neutral
    class REV,FRAG bad
    class ORDER,REENT warn
    class BOUND good
```

**Recommendation.** Document the shared nonce space; consume the nonce before the
external call in the 1271 branch.

---

## Non-findings (checked and clean)

| Check | Result |
|---|---|
| `_EIP712_DOMAIN_TYPEHASH` | ✅ matches independent keccak |
| `_PERMIT_TYPEHASH` | ✅ matches independent keccak |
| Cross-chain permit replay | ✅ `block.chainid` + `address(this)` in separator |
| Signature malleability / replay | ✅ nonce consumed in both overloads; OZ `ECDSA` rejects high-s |
| OFT `_credit`/`_debit` under pause | ✅ `endpoint` caller exemption is correct for LZ V2 |
| Mint access control | ✅ only in constructor; no public mint |
| `transferConfigurator` zero-address | ✅ reverts |

---

## Attack path (insider or compromised configurator key)

Requires 3-of-4 configurator Safe signers — not reachable by an outside attacker, but
this is the full extent of what that key can do:

1. `setPaused(true)` — all holder transfers revert; the float is frozen.
2. Configurator still sends, receives, and (with any pre-existing allowance)
   `transferFrom`s arbitrary third-party balances.
3. `owner` (4/5 of the same signers) can `setName`/`setSymbol` to anything.
4. `transferConfigurator` can rotate the role to an attacker-controlled address,
   making the exemption permanent and personal.

There is no timelock on any of these four steps.

```mermaid
flowchart TD
    K["Precondition<br/>3 of 4 configurator Safe signers<br/>4 of 5 owner signers are the SAME keys"]

    K --> S1["Step 1: setPaused true<br/>every holder transfer reverts<br/>the float is frozen"]
    S1 --> S2["Step 2: configurator keeps moving<br/>sends, receives, and transferFroms<br/>arbitrary third-party balances"]
    S2 --> S3["Step 3: owner calls setName / setSymbol<br/>rename FT to anything<br/>identity-spoofing primitive"]
    S3 --> S4["Step 4: transferConfigurator<br/>rotates the exemption to an<br/>attacker-controlled address"]

    S4 --> IMPACT["Attacker holds a fully functioning token<br/>while every other holder is frozen<br/>and the exemption is now permanent<br/>and personal"]

    S1 --> TL["No timelock on ANY step"]
    S2 --> TL
    S3 --> TL
    S4 --> TL

    K --> GATE["GATE<br/>Requires 3 of 4 Safe signers<br/>NOT reachable by an outside attacker"]
    GATE --> WHY["Still the honest trust model:<br/>3 keys, no timelock, no independent check,<br/>and 54% of supply sits in the<br/>exempt address"]

    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef good fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class K neutral
    class S1,S2,S3,S4,IMPACT,TL bad
    class GATE good
    class WHY warn
```

### Genesis state (FT-02)

```mermaid
flowchart LR
    DEPLOY["FT constructor runs"]
    DEPLOY --> MINT["if block.chainid == mintChainId<br/>_mint configurator, 10,000,000,000 FT<br/>L85"]
    DEPLOY --> PAUSE["_pause()<br/>L87"]

    MINT --> G1["One role owns 100% of supply"]
    PAUSE --> G2["All transfers disabled"]

    G1 --> G3["Combined with the FT-01 bypass,<br/>the configurator can move its own<br/>10B while nobody else moves anything"]
    G2 --> G3

    G3 --> G4["There is no moment at which holders<br/>have a claim the configurator<br/>cannot unilaterally override"]

    G4 --> G5["Unpausing REQUIRED an insider action<br/>after the premint"]

    classDef warn fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef bad fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef neutral fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class DEPLOY,MINT,PAUSE,G1,G2,G5 neutral
    class G3,G4 bad
```
