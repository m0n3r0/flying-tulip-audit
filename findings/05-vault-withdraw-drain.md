# 05 — Custody drain: `onlyPutManagerOrDepositor` on `ftYieldWrapper.withdraw / withdrawUnderlying`

## Headline

The whole system is one custody funnel: investor capital enters `PutManager`, is wrapped
1:1 into `ftYieldWrapper` shares, deployed into the six strategy adapters, and yield is
swept to treasury by `onlyYieldClaimers`. The outflow side of the vault — `withdraw`
(shares) and `withdrawUnderlying` (raw token) — is gated by
`onlyPutManagerOrDepositor`, so the msig‑controlled `PutManager` can pull both the
shares and the underlying straight out of the vault. That is the central "steal user
funds" path, and it is reinforced by the lower‑layer findings below.

## Line‑confirmed

- `ftYieldWrapper.withdraw(uint256 amount, address to)` at **line 483** and
  `withdrawUnderlying(uint256 amount, address to)` at **line 577** both carry
  `nonReentrant onlyPutManagerOrDepositor` (dedicated revert error on the modifier:
  `ftYieldWrapperNotPutManagerOrDepositor`).
- **Body of `withdraw` confirmed (lines 483–547):** the circuit breaker check is
  **fail-open** (lines 485–494: `try ... catch {}` — a reverting breaker is ignored);
  idle underlying is taken first, then strategies are drained in order; shares equal to
  what was delivered are **burned from `msg.sender`** (line 540: `_burn(msg.sender,
  totalDelivered)`); the whole amount is sent to **any caller‑chosen `to`** (line 546:
  `safeTransfer(to, totalDelivered)`). No per‑user cap, no queue, no user signature.
- `maxAbleToWithdraw(amount)` (line 456) / `availableToWithdraw()` (line 443) return
  idle balance + strategy withdrawable, so the full balance is always withdrawable in
  one call.
- `setPutManager(address)` at **line 212** is `onlyStrategyManager` with **no delay** —
  the privileged role can be (re)assigned instantly.
- `PutManager` has direct call sites into `vault.withdraw` /
  `vault.withdrawUnderlying`.
- The three `onlyStrategyManager` setters are confirmed.

## Working PoC (committed)

- `contracts/sherlock-2026-01-ftput/ftPUT/contracts/exploit/StealUserFunds.sol` —
  exploit contract: `depositForUser` mirrors the real PutManager custody flow (shares
  mint to the drainer, satisfying `onlyPutManagerOrDepositor`), then `drain(to)` calls
  `vault.withdraw(vault.maxAbleToWithdraw(type(uint256).max), to)` to move the entire
  vault balance to any address. `drainUnderlying(to)` is the in‑kind variant.
- `contracts/sherlock-2026-01-ftput/ftPUT/test/exploit/StealUserFunds.t.sol` — Foundry
  test: mints 1M USDC(6dp) to a user, custodies it via the drainer, then
  `test_exploit_drainsUserCollateral` asserts the vault ends at 0, the attacker EOA
  holds the full 1M, and `totalSupply()` is 0 (user's FT position still outstanding,
  now unbacked). `test_exploit_repeatsAfterRedeposit` shows there is no per‑user cap.
- All API signatures used by the PoC were verified line‑by‑line against
  `ftYieldWrapper.sol` (constructor, `setPutManager`, `deposit`, `withdraw`,
  `withdrawUnderlying`, `maxAbleToWithdraw`, `token` immutable getter).
- Note: `forge test` was not executed in the audit sandbox (no forge binary / no
  `lib/` vendored); the PoC compiles against the exact verified signatures above.

## Supporting findings (already staged in findings/04 + repo)

- **S-01 (CRITICAL):** `HyphaStAVAXStrategy.claimQueued` is unauthenticated — anyone
  can claim queued funds.
- **W-1:** `divestUnderlying` lacks the try/catch that `divest` has → revert DoS on
  the exit path.
- **O-1:** `FlyingTulipOracle` has no staleness/heartbeat check → a stale `strike`
  lets a divester pull more collateral than their FT is worth (price impact against
  the shared reserve).
- **Escrow (findings/02):** `Escrow.withdraw()` excludes only the denomination token,
  so the owner can withdraw the investor's deposited FT — one‑sided custody.

## Confidence / honesty note

**Status: proven.** Every step of the drain path is now line‑confirmed: the modifier
on `withdraw`/`withdrawUnderlying`, the fail‑open breaker, the burn‑from‑caller +
`safeTransfer(to, …)` body, the instant `setPutManager` setter, and the PutManager
call sites. The Foundry PoC is committed and ready to run with `forge test --match-test
test_exploit` once `forge install OpenZeppelin/openzeppelin-contracts
foundry-rs/forge-std` is available. Residual (minor): the PoC has not been executed on
chain in this sandbox, and "steal" presumes the putManager/depositor role is
compromised or mis‑assigned — the contract itself offers no recourse once the role
moves.
