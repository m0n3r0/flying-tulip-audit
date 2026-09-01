// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.30;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract Escrow {
    using SafeERC20 for IERC20;

    IERC20 public constant FT = IERC20(address(0x5DD1A7A369e8273371d2DBf9d83356057088082c));

    address public immutable owner;
    address public immutable recipient;
    IERC20 public immutable denomination;
    uint256 public immutable amountDenom;

    uint256 public withdrawnAmountDenom;

    constructor(address _owner, address _recipient, address _denomination, uint256 _amountDenom) {
        require(_owner != address(0), "owner=0");
        require(_recipient != address(0), "recipient=0");
        require(_denomination != address(0), "denom=0");

        owner = _owner;
        recipient = _recipient;
        denomination = IERC20(_denomination);
        amountDenom = _amountDenom;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call");
        _;
    }

    function withdraw(address token, uint amount) external onlyOwner {
        require(token != address(denomination), "use withdrawDenom");
        IERC20(token).safeTransfer(owner, amount);
    }

    function withdrawDenom(uint amount) external onlyOwner {
        withdrawnAmountDenom += amount;
        denomination.safeTransfer(owner, amount);
    }

    function withdrawFT(uint amount) external {
        require(msg.sender == recipient, "Only recipient can call");
        require(denomination.balanceOf(address(this)) + withdrawnAmountDenom >= amountDenom, "Not enough denom");
        FT.safeTransfer(recipient, amount);
    }
}
