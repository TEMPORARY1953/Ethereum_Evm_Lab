// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import {LabToken} from "../src/LabToken.sol";

interface VmDeploy {
    function envAddress(string calldata name) external view returns (address);
    function envOr(string calldata name, string calldata fallbackValue) external view returns (string memory);
    function startBroadcast(address signer) external;
    function stopBroadcast() external;
}

/// @notice Deploy only. Mint and transfer are separate, explicitly reviewed transactions.
contract Deploy {
    VmDeploy private constant vm = VmDeploy(address(uint160(uint256(keccak256("hevm cheat code")))));

    function run() external returns (LabToken token) {
        require(block.chainid == 31337 || block.chainid == 11155111, "Only Anvil or Sepolia");
        address owner = vm.envAddress("LAB_OWNER");
        string memory name = vm.envOr("TOKEN_NAME", string("Vmk Rulit Token"));
        string memory symbol = vm.envOr("TOKEN_SYMBOL", string("VMKRULIT"));
        vm.startBroadcast(owner);
        token = new LabToken(name, symbol, owner);
        vm.stopBroadcast();
    }
}
