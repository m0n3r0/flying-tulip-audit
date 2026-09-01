# Escrow (Trusted Token Transfer)

`src/Escrow.sol` implements a small, trusted escrow used to swap **Flying Tulip (FT)** tokens for an ERC20 **denomination** token.

## Summary

- **Owner (Flying Tulip)** funds the escrow with FT tokens.
- **Recipient** transfers the denomination token into the escrow.
- Once the escrow has received at least `amountDenom` denomination tokens (tracked even if the owner has already withdrawn them), the **recipient can withdraw FT**.

This design assumes a trusted flow: there is no price enforcement, timeouts, or partial-fill logic.

## Key Details

- **FT token address is fixed (same on every network)**: `Escrow.FT()` is hard-coded to `0x5DD1A7A369e8273371d2DBf9d83356057088082c`.
- The escrow does not have deposit functions; funding is done via standard ERC20 `transfer` to the escrow address.
- Transfers use OpenZeppelin `SafeERC20` to safely handle non-standard ERC20 return values.
- `withdrawnAmountDenom` tracks denomination tokens already withdrawn by the owner so the recipient can still withdraw FT after payment is received.

## Contract Interface

- `withdraw(address token, uint256 amount)` (owner only): withdraw any token except the denomination token.
- `withdrawDenom(uint256 amount)` (owner only): withdraw denomination tokens and increment `withdrawnAmountDenom`.
- `withdrawFT(uint256 amount)` (recipient only): withdraw FT once `denomination.balanceOf(escrow) + withdrawnAmountDenom >= amountDenom`.

## Development

### Install

```sh
git submodule update --init --recursive
```

### Build

```sh
forge build
```

### Test

```sh
forge test -vvv
```

### Coverage

```sh
forge coverage
```

Note: `src/Escrow.sol` is excluded from `forge fmt` to preserve the audited source exactly.

## Deploy

Deployment uses `script/DeployEscrow.s.sol:DeployEscrowScript`.

Environment variables read by the script:

- `PRIVATE_KEY` (deployer key)
- `ESCROW_OWNER`
- `ESCROW_RECIPIENT`
- `ESCROW_DENOMINATION`
- `ESCROW_AMOUNT_DENOM`

Example:

```sh
export PRIVATE_KEY=...
export ESCROW_OWNER=0x...
export ESCROW_RECIPIENT=0x...
export ESCROW_DENOMINATION=0x...
export ESCROW_AMOUNT_DENOM=100000000000000000000

forge script script/DeployEscrow.s.sol:DeployEscrowScript \
  --rpc-url $RPC_URL \
  --broadcast
```
