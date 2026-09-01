// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.30;

import {Test} from "forge-std/Test.sol";

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import {Escrow} from "src/Escrow.sol";
import {MockERC20} from "./mocks/MockERC20.sol";

contract EscrowTest is Test {
    address internal constant FT_ADDRESS = 0x5DD1A7A369e8273371d2DBf9d83356057088082c;

    uint256 internal constant AMOUNT_DENOM = 100e18;

    address internal owner;
    address internal recipient;
    address internal stranger;

    Escrow internal escrow;
    MockERC20 internal denom;

    function setUp() public {
        owner = makeAddr("owner");
        recipient = makeAddr("recipient");
        stranger = makeAddr("stranger");

        denom = new MockERC20("Denomination", "DENOM");
        escrow = new Escrow(owner, recipient, address(denom), AMOUNT_DENOM);
    }

    function test_constructor_setsFields() public {
        assertEq(address(escrow.FT()), FT_ADDRESS);
        assertEq(escrow.owner(), owner);
        assertEq(escrow.recipient(), recipient);
        assertEq(address(escrow.denomination()), address(denom));
        assertEq(escrow.amountDenom(), AMOUNT_DENOM);
        assertEq(escrow.withdrawnAmountDenom(), 0);
    }

    function test_constructor_revertsWhenOwnerZero() public {
        vm.expectRevert(bytes("owner=0"));
        new Escrow(address(0), recipient, address(denom), AMOUNT_DENOM);
    }

    function test_constructor_revertsWhenRecipientZero() public {
        vm.expectRevert(bytes("recipient=0"));
        new Escrow(owner, address(0), address(denom), AMOUNT_DENOM);
    }

    function test_constructor_revertsWhenDenominationZero() public {
        vm.expectRevert(bytes("denom=0"));
        new Escrow(owner, recipient, address(0), AMOUNT_DENOM);
    }

    function test_withdraw_revertsWhenNotOwner() public {
        MockERC20 other = new MockERC20("Other", "OTHER");
        other.mint(address(escrow), 1);

        vm.prank(stranger);
        vm.expectRevert(bytes("Only owner can call"));
        escrow.withdraw(address(other), 1);
    }

    function test_withdraw_revertsWhenTokenIsDenomination() public {
        vm.prank(owner);
        vm.expectRevert(bytes("use withdrawDenom"));
        escrow.withdraw(address(denom), 1);
    }

    function test_withdraw_transfersToOwner() public {
        MockERC20 other = new MockERC20("Other", "OTHER");
        other.mint(address(escrow), 123);

        vm.prank(owner);
        escrow.withdraw(address(other), 123);

        assertEq(other.balanceOf(address(escrow)), 0);
        assertEq(other.balanceOf(owner), 123);
    }

    function test_withdrawDenom_revertsWhenNotOwner() public {
        denom.mint(address(escrow), 1);

        vm.prank(stranger);
        vm.expectRevert(bytes("Only owner can call"));
        escrow.withdrawDenom(1);
    }

    function test_withdrawDenom_updatesAccountingAndTransfers() public {
        denom.mint(address(escrow), 250e18);

        vm.prank(owner);
        escrow.withdrawDenom(100e18);

        assertEq(escrow.withdrawnAmountDenom(), 100e18);
        assertEq(denom.balanceOf(owner), 100e18);
        assertEq(denom.balanceOf(address(escrow)), 150e18);
    }

    function test_withdrawFT_revertsWhenNotRecipient() public {
        vm.prank(stranger);
        vm.expectRevert(bytes("Only recipient can call"));
        escrow.withdrawFT(1);
    }

    function test_withdrawFT_revertsWhenNotEnoughDenom() public {
        vm.prank(recipient);
        vm.expectRevert(bytes("Not enough denom"));
        escrow.withdrawFT(1);
    }

    function test_withdrawFT_transfersFTOnceDenomSatisfied() public {
        denom.mint(recipient, AMOUNT_DENOM);
        vm.prank(recipient);
        assertTrue(denom.transfer(address(escrow), AMOUNT_DENOM));

        uint256 amount = 10e18;
        bytes memory callData = abi.encodeWithSelector(IERC20.transfer.selector, recipient, amount);
        vm.mockCall(FT_ADDRESS, callData, abi.encode(true));
        vm.expectCall(FT_ADDRESS, callData);

        vm.prank(recipient);
        escrow.withdrawFT(amount);
    }

    function test_withdrawFT_allowsAfterOwnerWithdrawsDenom() public {
        denom.mint(recipient, AMOUNT_DENOM);
        vm.prank(recipient);
        assertTrue(denom.transfer(address(escrow), AMOUNT_DENOM));

        vm.prank(owner);
        escrow.withdrawDenom(AMOUNT_DENOM);

        uint256 amount = 10e18;
        bytes memory callData = abi.encodeWithSelector(IERC20.transfer.selector, recipient, amount);
        vm.mockCall(FT_ADDRESS, callData, abi.encode(true));

        vm.prank(recipient);
        escrow.withdrawFT(amount);
    }
}
