# Flying Tulip contest details

- Join [Sherlock Discord](https://discord.gg/MABEWyASkp)
- Submit findings using the **Issues** page in your private contest repo (label issues as **Medium** or **High**)
- [Read for more details](https://docs.sherlock.xyz/audits/watsons)

# Q&A

### Q: On what chains are the smart contracts going to be deployed?
Ethereum, base, BSC (binance chain), Avalanche, sonic
___

### Q: If you are integrating tokens, are you allowing only whitelisted tokens to work with the codebase or any complying with the standard? Are they assumed to have certain properties, e.g. be non-reentrant? Are there any types of [weird tokens](https://github.com/d-xo/weird-erc20) you want to integrate?
ftPUT whitelists tokens, for any specific network it may used the following:

-native wrapped token e.g sonic-> wrapped sonic or wETH, wBNB (all networks)
-USDC (all networks, except BSC)
-USDT (Ethereum, Avalanche)
-USDS (Ethereum)
-USDTB (Ethereum) 
-USDE (Ethereum)

NOTE: under script/config/deployments.toml has a list of each network specific tokens used in current production setup plan. The lists of tokens inside deployment.toml will be referred to during judging.

Also the FT token itself is an OFT token based on the LayerZero network 0x5DD1A7A369e8273371d2DBf9d83356057088082c to enable multichain capabilities
___

### Q: Are there any limitations on values set by admins (or other roles) in the codebase, including restrictions on array lengths?
The privileged roles like msig admin are fully trusted, msig can upgrade implementation of putManager and pFT.

The other roles are partially trusted to specific actions.

The roles and privileges are detailed here:
ftPUT/PRIVILEGES.md in the contest repo

The msig addresses are listed here:
https://docs.flyingtulip.com/risks/multisigs/

The roles are considered trusted when completing their tasks and roles and won't harm the users and/or the protocol. However, they shouldn't be able to overstep or bypass their restrictions. If they manage to do that and it leads to Medium/High impact, it can be considered a valid issue.

___

### Q: Are there any limitations on values set by admins (or other roles) in protocols you integrate with, including restrictions on array lengths?
ftPUT integrates the AAVE oracle on each of the networks and adds price bounds to the read values to protect from extreme values out of range for sale purposes

ftPUT/contracts/FlyingTulipOracle.sol


___

### Q: Is the codebase expected to comply with any specific EIPs?
not comply specifically, but there is an ERC-7265 inspired implementation of a circuit breaker pattern as the production phase is rolled out this works like a guarded launch to ensure complete withdrawal of TVL is not possible. EIP-violations are not considered valid issues as contracts are not intended to comply with any specific EIP.

ftPUT/contracts/cb/CircuitBreaker.sol
___

### Q: Are there any off-chain mechanisms involved in the protocol (e.g., keeper bots, arbitrage bots, etc.)? We assume these mechanisms will not misbehave, delay, or go offline unless otherwise specified.
N/A
___

### Q: What properties/invariants do you want to hold even if breaking them has a low/unknown impact?
The documented invariants can be found 
ftPUT/test/invariants/INVARIANTS.md
___

### Q: Please discuss any design choices you made.
The FT token is an OFT token with multichain support via the LayerZero stack support.

Regarding the circuitbreaker (CB) it covers all the inflows/outflows of the yieldWrappers to keep track of the rate limits configured per token asset, since the CB was added late stage in development cycle to keep the change as low impact as possible the only value transfer it could not cover was the "putManager.withdrawFT()" function, by design choice to lower impact on CB integration changes, if an issue is found on this flow the putManager can be upgraded so that the CB can cover that flow as well (if any issue related to this flow can lead to Medium/High impact, it can be considered a valid issue).

There are several caps on all operations that can be added/removed to manage risk on TVL as well as whitelisting specific strategies and tokens. The system is intended to use low-risk yield options for the capital managed. The protocol will invest in strategies that cannot suffer a loss, and the strategies will be low-risk yield.
___

### Q: Please provide links to previous audits (if any) and all the known issues or acceptable risks.
known issues/risks accepted from past audits: [description of issue]: [risk accepted by FT description]

- rounding issues for low decimal tokens for low amounts of FT (0.01 FT): When divesting and withdrawing, the protocol now reverts if collateralFromFT() returns 0. This limits the harm to both the user and the protocol to half the amount.
Additionally, the precision of ftPerUSD has been increased to 10^-8. The example computation becomes
(with ftPerUSD = 1e9) `collateralFromFt = ftAmount * (1e8*1e8*1e8)/(1e13*1e9*1e18) = ftAmount * 1e24/1e40`. This does not change the threshold of 0.01 FT. The two code changes above still allow some dust to be accrued/not divested when the amount is not a multiple of the threshold.
Finally, amountRemaining is now zeroed when burning, but no additional funds are transfered.
- losses not handle: Operational mitigation and disclosures; wrapper enforces exact withdrawals and defensive selection,
but protocol-level loss handling and backstops are out-of-scope for this codebase
- short delays on timelock changes: In this repo, short delays are intentional for testing. In production, we configure non-zero timelocks for role/strategy updates as part of deployment process and governance policy.
- malicious strategy manager cannot be removed: Two-step role rotation is retained; emergency procedures (pause/rotation by multisig, MEV-bundled atomic updates) are documented for production ops.
- yield claimer must be responsive in order to recover funds: Description of changes: Maintain primary + subYieldClaimer, operational SLOs/monitoring, and governance intervention procedures. Code remains non-reentrant and exact-withdrawal hardened
- AaveStrategy.availableToWithdraw does not check reserves: Description of changes: Defensive try/catch on liquidity views and exact withdraws reduce exposure. Pool pause is handled operationally via monitoring and wrapper selection.
- Caps updates can be front-run: Apply caps during paused windows or with pre-announced enforcement;
optional use of pause during configuration changes.
- Non empty strategy can be removed: mitigated by ops off chain monitoring, can be added back and yield claimed.



___

### Q: Please list any relevant protocol resources.
https://docs.flyingtulip.com/

https://flyingtulip.com/
___

### Q: Additional audit information.
Something that needs further validation are the in/out flows in regards to the integration with circuit breaker since this was added post audit as an additional security layer, assumptions and design choices stated above apply, regarding withdrawFT not being covered as design choice.


# Audit scope

[ftPUT @ 193074610e69365161610de3163d7955312e7557](https://github.com/flyingtulipdotcom/ftPUT/tree/193074610e69365161610de3163d7955312e7557)
- [ftPUT/contracts/cb/CircuitBreaker.sol](ftPUT/contracts/cb/CircuitBreaker.sol)
- [ftPUT/contracts/FlyingTulipOracle.sol](ftPUT/contracts/FlyingTulipOracle.sol)
- [ftPUT/contracts/ftACL.sol](ftPUT/contracts/ftACL.sol)
- [ftPUT/contracts/ftYieldWrapper.sol](ftPUT/contracts/ftYieldWrapper.sol)
- [ftPUT/contracts/interfaces/IAaveOracle.sol](ftPUT/contracts/interfaces/IAaveOracle.sol)
- [ftPUT/contracts/interfaces/IAavePoolAddressesProvider.sol](ftPUT/contracts/interfaces/IAavePoolAddressesProvider.sol)
- [ftPUT/contracts/interfaces/IAavePoolInstance.sol](ftPUT/contracts/interfaces/IAavePoolInstance.sol)
- [ftPUT/contracts/interfaces/ICircuitBreaker.sol](ftPUT/contracts/interfaces/ICircuitBreaker.sol)
- [ftPUT/contracts/interfaces/IERC20MetadataBurnable.sol](ftPUT/contracts/interfaces/IERC20MetadataBurnable.sol)
- [ftPUT/contracts/interfaces/IFlyingTulipOracle.sol](ftPUT/contracts/interfaces/IFlyingTulipOracle.sol)
- [ftPUT/contracts/interfaces/IftACL.sol](ftPUT/contracts/interfaces/IftACL.sol)
- [ftPUT/contracts/interfaces/IftPut.sol](ftPUT/contracts/interfaces/IftPut.sol)
- [ftPUT/contracts/interfaces/IftYield.sol](ftPUT/contracts/interfaces/IftYield.sol)
- [ftPUT/contracts/interfaces/IftYieldWrapper.sol](ftPUT/contracts/interfaces/IftYieldWrapper.sol)
- [ftPUT/contracts/interfaces/IStrategy.sol](ftPUT/contracts/interfaces/IStrategy.sol)
- [ftPUT/contracts/pFT.sol](ftPUT/contracts/pFT.sol)
- [ftPUT/contracts/PutManager.sol](ftPUT/contracts/PutManager.sol)
- [ftPUT/contracts/strategies/AaveStrategy.sol](ftPUT/contracts/strategies/AaveStrategy.sol)


#   2 0 2 6 - 0 1 - f l y i n g - t u l i p - z a k i 9 5 0 1 - m a i n  
 