# flying-tulip-audit

Independent security + economic review of **Flying Tulip** (Andre Cronje).
Date: 2026-09-02.

**Start here:** [`reports/FINAL_REPORT.md`](reports/FINAL_REPORT.md)

## Headline conclusions

1. **The published code is fine; the important code is not published.** `FT.sol` is
   competent — no arithmetic, reentrancy, or signature-replay bugs found. But
   `PutManager`, the contract holding 100% of backing capital, is **closed source**.
2. **Best contract finding: `Escrow.withdraw()` bypasses the contract's only
   protection.** It excludes just the denomination token, so the owner can withdraw the
   FT deposited for the investor. The "escrow" is one-sided custody.
3. **The yield reasoning has a hard ceiling.** If principal is truly never spent and
   unlevered, yield is at most the ~3% the collateral earns (their own benchmark
   table), minus the team's operating budget, which takes **first call**. Realistic
   surplus is ~0.16% of FDV. The buyback that actually scales is funded by **other
   holders' principal**, and it executes into a **$2.1M float**.
4. **Docs say 10B supply; chain says 1.199B.** An ~8.8B gap.

## Structure

- `research/01-protocol-overview.md` — architecture, tokenomics, products, yield claims
- `research/02-onchain-facts.md` — verified supply, distribution, roles, market data
- `findings/01-FT-token.md` — FT.sol review + attack path
- `findings/02-Escrow.md` — Escrow.sol review
- `findings/03-economics-high-yield.md` — the yield critique
- `contracts/` — upstream source (cloned from `github.com/flyingtulipdotcom`)
- `scripts/keccak.py` — pure-Python keccak-256 used to verify EIP-712 typehashes

## Method

Manual source review plus live RPC verification across Ethereum, BSC, Base, Avalanche
and Sonic. All on-chain numbers in `research/02-onchain-facts.md` were read live and are
reproducible.

## Disclaimer

Research notes only. Not investment advice. Not a substitute for a professional audit.
No exploit code is included; findings are descriptive.
