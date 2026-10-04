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

- `ftYieldWrapper.withdraw` / `withdrawUnderlying` carry `onlyPutManagerOrDepositor`
  (dedicated revert error on the modifier).
- `PutManager` has direct call sites into `vault.withdraw` /
  `vault.withdrawUnderlying`.
- The three `onlyStrategyManager` setters are confirmed.

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

Verified directly: the modifiers, the three `onlyStrategyManager` setters, and the
`PutManager → vault.withdraw` call sites. The one step still inferred (not
line‑confirmed) is the exact body of the vault's `withdraw` / `withdrawUnderlying` at
lines ~280–745 — the presence of `onlyPutManagerOrDepositor` plus its dedicated error
strongly implies it gates that path. Confirming that body is the single remaining step
to turn "very likely" into "proven" (that was option (a): line‑confirm + Foundry drain
PoC).
