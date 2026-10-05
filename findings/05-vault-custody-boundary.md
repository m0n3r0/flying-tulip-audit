# 05 — Vault custody boundary: withdrawal mechanics, role changes, fail-open breaker

**Status: Informational (operational hardening). Not a fund-theft finding.**

Revision 2026-10-05: corrected after full mechanics review and execution; an earlier
draft ("custody drain", "central steal user funds path") overstated what the code
permits and cited stale line numbers — both fixed below.

## Bottom line

`ftYieldWrapper.withdraw` / `withdrawUnderlying` are gated by `onlyPutManagerOrDepositor`
and pay out to any caller-chosen `to` — but every exit **burns the caller's own wrapper
shares** (`_burn(msg.sender, …)`, lines 565 / 641). Extraction is therefore bounded by
the caller's share balance, and shares are acquired only by paying for them 1:1 through
`deposit()`. No role grants access to someone else's shares. In the deployed system all
shares sit with the `PutManager` proxy, which services users through FT accounting — so
no party outside custody can move the backing, and the "drain" framing does not survive
the mechanics.

## Observations (informational)

1. **Instant, single-step wrapper role changes.** `setPutManager` (line 212),
   `setDepositor` (line 218, which also skips the zero-address check its siblings have)
   and `setCircuitBreaker` (line 226) are `onlyStrategyManager`, with no delay and no
   pending/confirm step — contrast the `yieldClaimer` / `strategyManager` / `treasury`
   rotations, which are 2-step. If the `strategyManager` role is compromised or misused,
   put-servicing flows freeze: the newly-appointed `putManager` holds no shares (the
   burn reverts), while the actual share-holder (`PutManager`) fails the role check.
   Recoverable by governance — re-point the role, or rotate `strategyManager` through
   its pending/confirm flow — but with zero timelock at this layer.
2. **Fail-open circuit-breaker check on both exits.** The breaker call is wrapped in
   `try/catch {}` and reverts are ignored (lines 485–495 for `withdraw`, 586–595 for
   `withdrawUnderlying`). A breaker that reverts instead of returning
   `(false, available)` is silently bypassed, so the rate limit does not hold for
   share-holding callers. Cannot move third-party funds; hardening item.
3. **`withdrawUnderlying` never touches idle underlying** — in-kind exits draw only from
   strategies and revert when none can deliver (verified: reverts before the burn even
   for a share-holding caller when there are no strategies). Operational detail for
   in-kind servicing.

## Mechanics, line-checked (ftYieldWrapper.sol)

- Burn from caller, payout to any `to`: `_burn(msg.sender, totalDelivered)` at line 565
  (`withdraw`), payout `safeTransfer(to, totalDelivered)` at line 572; the in-kind
  variant burns at line 641. **Extraction ≤ caller's share balance.**
- Shares mint 1:1 only via `deposit()` (lines 468–481; mint at 479) to the caller,
  against underlying the caller actually pays. Nothing mints shares to a role, and no
  path burns or moves another account's shares.
- `maxAbleToWithdraw` / `availableToWithdraw` report liquidity only (no queue, no
  per-user cap) — liquidity statements cannot conjure shares for a caller who has none.

## Why the custody layer stays whole (PutManager.sol / pFT.sol)

- All wrapper shares are held by the `PutManager` proxy: `invest()` pulls collateral and
  calls `vault.deposit()` (PutManager.sol:399–406), so shares mint to `PutManager`.
- Outflows route strictly by FT accounting: `divest` / `divestUnderlying` pay the caller
  after `pFT` ownership checks (PutManager.sol:534 / :559; pFT.sol:187 / :231); the msig
  pull (`withdrawDivestedCapital`, `onlyMsig`) is clamped to `capitalDivesting` and pays
  `msig` — the documented design for FT redemption (PutManager.sol:444–459).
- No function in the custody contracts passes an arbitrary `to` to the vault. Redirecting
  custody to an arbitrary address requires replacing the custodian's own logic — e.g. the
  msig (UUPS proxy admin, PutManager.sol:26 / :667) upgrading to an implementation that
  calls `vault.withdraw(x, anywhere)` while the proxy keeps both the shares and the role.
  That is the standard trusted-governance boundary, not an externally triggerable bug.

## Empirical record

Executed with forge 1.8.4 / solc 0.8.30 (deps at foundry.lock revs), repro run locally
against these sources:

- The committed demo
  (`contracts/sherlock-2026-01-ftput/ftPUT/contracts/exploit/StealUserFunds.sol` + test)
  works **only** because the demo contract is itself the custodian: it takes the user's
  funds (with the user's approval) and holds the shares minted for that deposit, then
  redeems them to a third address. A custody-boundary demo — circular by construction,
  not theft from a non-custodian. The files remain in the tree as documentation; their
  comments now say exactly this.
- Probe 1 — freshly-appointed `putManager`, zero shares: `withdraw` reverts
  `ERC20InsufficientBalance(caller, 0, amount)`; `withdrawUnderlying` reverts
  `ftYieldWrapperInsufficientLiquidity` (in-kind exits never touch idle funds).
  Nothing moves.
- Probe 2 — role re-pointed to a stranger: the actual share-holder is locked out (the
  freeze above); restoring the role resumes operations; no funds lost.
- Probe 3 — surplus in the vault: the demo's own `drain()` reverts
  (`ERC20InsufficientBalance`) — "entire vault balance" only ever equals "the caller's
  own shares".

## Related, tracked separately

S-01 (`HyphaStAVAXStrategy.claimQueued` unauthenticated), W-1 (`divestUnderlying`
try/catch asymmetry), O-1 (oracle staleness), Escrow (findings/02) — see findings/04.

## Verification / falsifiers

Reviewed against `ftYieldWrapper.sol`, `PutManager.sol`, `pFT.sol`; all line references
verified in the current tree. Falsifiers actively searched for and not found: obtaining
wrapper shares without paying, an arbitrary-`to` outflow in the custody contracts, or a
path burning another account's shares. If any of those appears, this note should be
revisited.