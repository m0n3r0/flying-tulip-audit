# Known Issues

This document lists security issues that are **already known** to the FT team.
Issues described here are considered **out of scope**.

**Note:**: some issues may be reported and in triage process but not yet listed, those are also considered duplicate and out of scope.

Submission, eligibility, and reward rules are governed by the FT bug bounty program on
Sherlock — see [`README.md`](./README.md). This list only documents what is already
known; how it affects a given submission is determined by the rules on the bounty
platform.

> **Status legend**
> - **Acknowledged** — confirmed; residual risk accepted.
> - **Mitigated** — partially addressed in code and/or by operational controls; residual risk accepted.
> - **By design** — intended behavior given current architecture / deployment model.

**Last updated:** 2026-07-16

---

## Table of contents

- [PutManager](#putmanager)
  - [PM-01 — Rounding loss for low-decimal tokens at small FT amounts](#pm-01--rounding-loss-for-low-decimal-tokens-at-small-ft-amounts)
  - [PM-02 — Protocol-level losses are not handled on-chain](#pm-02--protocol-level-losses-are-not-handled-on-chain)
  - [PM-03 — Missing slippage protection in `PutManager.invest()`](#pm-03--missing-slippage-protection-in-putmanagerinvest)
- [Strategy Management & Roles](#strategy-management--roles)
  - [SM-01 — Short delays on timelock changes](#sm-01--short-delays-on-timelock-changes)
  - [SM-02 — Malicious strategy manager cannot be removed promptly](#sm-02--malicious-strategy-manager-cannot-be-removed-promptly)
  - [SM-03 — Caps updates can be front-run](#sm-03--caps-updates-can-be-front-run)
  - [SM-04 — Non-empty strategy can be removed](#sm-04--non-empty-strategy-can-be-removed)
- [AaveStrategy](#aavestrategy)
  - [AAVE-01 — `availableToWithdraw` does not check pool reserves](#aave-01--availabletowithdraw-does-not-check-pool-reserves)
- [YieldClaimer](#yieldclaimer)
  - [YC-01 — Yield claimer must be responsive to recover funds](#yc-01--yield-claimer-must-be-responsive-to-recover-funds)
- [LeverageRfqEngine](#leveragerfqengine)
  - [LEV-01 — Cancel and fill session calls share the order hash by design](#lev-01--cancel-and-fill-session-calls-share-the-order-hash-by-design)
- [CircuitBreaker (ftDNMM)](#circuitbreaker-ftdnmm)
  - [CB-01 — Circuit-breaker capacity can lag same-block TVL changes](#cb-01--circuit-breaker-capacity-can-lag-same-block-tvl-changes)
- [pFTMarketplace](#pftmarketplace)
  - [MKT-01 — `acceptBuyOffer`: Put snapshot not bound to the signed offer](#mkt-01--acceptbuyoffer-put-snapshot-not-bound-to-the-signed-offer)
  - [MKT-02 — Stale direct listings after PUT state changes](#mkt-02--stale-direct-listings-after-put-state-changes)
  - [MKT-03 — Native payout recovery can fail for rejecting contracts](#mkt-03--native-payout-recovery-can-fail-for-rejecting-contracts)

---

## PutManager

### PM-01 — Rounding loss for low-decimal tokens at small FT amounts

**Status:** Mitigated

When divesting and withdrawing very small amounts of FT (≈ 0.01 FT) denominated in
low-decimal collateral tokens, integer rounding in the collateral conversion can
truncate to zero.

Mitigations in place:

- When divesting and withdrawing, the protocol now **reverts if `collateralFromFT()`
  returns 0**. This limits the harm to both the user and the protocol to at most half
  the threshold amount.
- The precision of `ftPerUSD` has been increased to `10^-8`. The example computation
  becomes (with `ftPerUSD = 1e9`):

  ```
  collateralFromFt = ftAmount * (1e8 * 1e8 * 1e8) / (1e13 * 1e9 * 1e18)
                   = ftAmount * 1e24 / 1e40
  ```

  This does **not** change the threshold of 0.01 FT.
- `amountRemaining` is now zeroed when burning, but no additional funds are transferred.

**Residual risk:** The two code changes above still allow some dust to be accrued / not
divested when the amount is not a multiple of the threshold. This residual dust is
acknowledged and accepted.

---

### PM-02 — Protocol-level losses are not handled on-chain

**Status:** Acknowledged

The codebase does not implement protocol-level loss handling or backstops. Reported
losses are addressed through operational mitigation and disclosures; the wrapper
enforces exact withdrawals and defensive strategy selection.

Protocol-level loss handling and backstops are **out of scope for this codebase**.

---

### PM-03 — Missing slippage protection in `PutManager.invest()`

**Status:** Mitigated

`PutManager.invest()` does not enforce on-chain slippage bounds.

**Mitigation:** Handled operationally — investing is performed predominantly in stable
assets during sale, and within oracle-bounded price ranges.

---

## Strategy Management & Roles

### SM-01 — Short delays on timelock changes

**Status:** By design (testing) / Mitigated (production)

In this repository, short timelock delays are **intentional for testing**.

**Production:** Non-zero timelocks for role/strategy updates are configured as part of
the deployment process and governance policy.

---

### SM-02 — Malicious strategy manager cannot be removed promptly

**Status:** Mitigated

A compromised or malicious strategy manager cannot be instantly revoked on-chain.

**Mitigation:** Two-step role rotation is retained. Emergency procedures — pause /
rotation by multisig, and MEV-bundled atomic updates — are documented for production
operations.

---

### SM-03 — Caps updates can be front-run

**Status:** Mitigated

Cap updates are observable in the mempool and can be front-run before they take effect.

**Mitigation:** Apply caps during paused windows or with pre-announced enforcement;
optionally use pause during configuration changes.

---

### SM-04 — Non-empty strategy can be removed

**Status:** Mitigated

A strategy that still holds funds can be removed.

**Mitigation:** Mitigated by off-chain operational monitoring. A removed strategy can be
added back and its yield claimed.

---

## AaveStrategy

### AAVE-01 — `availableToWithdraw` does not check pool reserves

**Status:** Mitigated

`AaveStrategy.availableToWithdraw` does not account for available liquidity in the
underlying Aave pool.

**Mitigation:** Defensive `try/catch` on liquidity views and exact withdrawals reduce
exposure. Pool pause is handled operationally via monitoring and wrapper selection.

---

## YieldClaimer

### YC-01 — Yield claimer must be responsive to recover funds

**Status:** Mitigated

Recovery of funds depends on a responsive yield claimer.

**Mitigation:** Maintain a primary **and** a `subYieldClaimer`, operational SLOs /
monitoring, and governance intervention procedures. Code remains non-reentrant and
exact-withdrawal hardened.

---

## LeverageRfqEngine

### LEV-01 — Cancel and fill session calls share the order hash by design

**Status:** By design

`LeverageRfqEngine` intentionally uses `_orderStructHash(order)` as the session
`dataHash` for both `cancelOrderWithSession()` and session-based fill entrypoints. A
cancel-order hash and an `openLeverage` / fill hash are therefore interchangeable for
the same order at the contract boundary.

**Bounds / rationale:** Executors are within the trusted boundary and the executor is
fixed in the signed `SessionCall`; it cannot be substituted after signing. Even outside
that trust model, a compromised executor could only choose to use the already-authorized
order hash to fill the exact order the user requested instead of cancelling it. The same
nonce is consumed on successful execution, sessions are valid for at most one day, and
session limits, PositionsManager allowances, health factor, liquidity, and cap checks
still apply. The stale-order variant is accepted as bounded because an open order that
was fillable and adverse would already be fillable through the intended fill path, and
otherwise still requires a valid session and the originally fixed executor. Sharing the
hash is an intentional contract-size tradeoff.

---

## CircuitBreaker (ftDNMM)

### CB-01 — Circuit-breaker capacity can lag same-block TVL changes

**Status:** Acknowledged

Circuit-breaker / rate-limiter capacity is tracked as a buffer that is passively updated
as a function of elapsed time. When the underlying reference value (e.g. wrapper TVL) is
reduced within the same block as a protected outflow — for instance by an authorized
liquidation or bypass path that moves TVL without touching limiter state — the
state-changing update can compute the new, lower cap but return early because no time has
elapsed, before it clamps the stored buffer down to that cap. Until a later timestamp
triggers a normal update, the buffer still reflects the higher pre-decrease reference
value, so an outflow may consume more capacity than the current value should allow.

A related symptom of the same mechanism: a read-only capacity view that always clamps to
the current reference value can disagree with the state-changing path within the same
block, because only the state-changing path takes the zero-elapsed-time early return.

**Class of issue / bounds:** This is a general property of elapsed-time-driven limiter
accounting rather than a specific route or version. It requires a privileged or authorized
action to move the reference value within a block; it is not reachable by an arbitrary
external caller. The discrepancy is transient — bounded to a single block timestamp — and
self-corrects on the next update at a later timestamp. Limiter implementations that
recompute and clamp the buffer from the current reference value *before* the
zero-elapsed-time early return, and integrations that always pass the current pre-outflow
reference value (including any earlier same-transaction decrease), do not exhibit the
stale-capacity behavior.

---

## pFTMarketplace

### MKT-01 — `acceptBuyOffer`: Put snapshot not bound to the signed offer

**Status:** Mitigated

`expectedPutHash` is a **caller-supplied argument** rather than being committed in the
EIP-712 `BuyOffer`. A token owner could therefore divest to shrink the Put before
accepting and still pass the recomputed hash, leaving the buyer's signed
`minAmountRemaining` / `minFt` / `minStrike` as the only on-chain floor.

**Mitigation / bounds:** UI and backend guardrails lower the likelihood and impact.
Exposure is otherwise bounded by the buyer's signed minimums (an accepted loss) and by
position size.

---

### MKT-02 — Stale direct listings after PUT state changes

**Status:** Mitigated

Direct listings do not store a listing-time PUT hash. If a seller changes `ft` /
`amountRemaining` after listing, the listing can still execute when a buyer supplies the
new current hash.

**Mitigation:** Mitigated by infrastructure-side checks.

---

### MKT-03 — Native payout recovery can fail for rejecting contracts

**Status:** Mitigated

The marketplace continues native sales when a seller's ETH payout fails, but recovery
only retries sending ETH to the same `msg.sender`. Contract sellers or fee recipients
that permanently reject ETH can have proceeds stuck.

**Mitigation:** Infrastructure / UI only supports EOA sellers.
