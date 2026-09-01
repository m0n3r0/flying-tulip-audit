// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.30;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";

import {Escrow} from "src/Escrow.sol";

contract DeployEscrowScript is Script {
    function run() external returns (Escrow deployed) {
        address owner = vm.envAddress("ESCROW_OWNER");
        address recipient = vm.envAddress("ESCROW_RECIPIENT");
        address denomination = vm.envAddress("ESCROW_DENOMINATION");
        uint256 amountDenom = vm.envUint("ESCROW_AMOUNT_DENOM");

        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(deployerPrivateKey);
        deployed = new Escrow(owner, recipient, denomination, amountDenom);
        vm.stopBroadcast();

        console2.log("Escrow deployed at", address(deployed));
    }
}

