// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import {LabToken} from "../src/LabToken.sol";
import {IERC20} from "../src/IERC20.sol";

// Only the real Foundry cheatcode ABI is declared here. No forge-std dependency.
interface Vm {
    function prank(address sender) external;
    function expectRevert(bytes calldata data) external;
    function expectEmit(bool topic1, bool topic2, bool topic3, bool data) external;
}

contract LabTokenTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address private constant ALICE = address(0xA11CE);
    address private constant BOB = address(0xB0B);
    address private constant SPENDER = address(0xCAFE);
    uint256 private constant UNIT = 1e18;
    LabToken private token;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    function setUp() public {
        token = new LabToken("Vmk Rulit Token", "VMKRULIT", address(this));
    }

    function testMetadata() public view {
        require(keccak256(bytes(token.name())) == keccak256("Vmk Rulit Token"), "name");
        require(keccak256(bytes(token.symbol())) == keccak256("VMKRULIT"), "symbol");
        require(token.decimals() == 18, "decimals");
        require(token.owner() == address(this), "owner");
    }

    function testCustomMetadata() public {
        LabToken custom = new LabToken("Custom Name", "CUSTOM", ALICE);
        require(keccak256(bytes(custom.name())) == keccak256("Custom Name"), "custom name");
        require(keccak256(bytes(custom.symbol())) == keccak256("CUSTOM"), "custom symbol");
    }

    function testInitialState() public view {
        require(token.totalSupply() == 0, "initial supply");
        require(token.balanceOf(ALICE) == 0, "initial balance");
        require(token.allowance(ALICE, SPENDER) == 0, "initial allowance");
    }

    function testMintSupplyBalanceAndEvent() public {
        vm.expectEmit(true, true, false, true);
        emit Transfer(address(0), ALICE, 2 * UNIT);
        token.mint(ALICE, 2 * UNIT);
        token.mint(BOB, UNIT);
        require(token.totalSupply() == 3 * UNIT, "mint supply");
        require(token.balanceOf(ALICE) == 2 * UNIT, "mint alice");
        require(token.balanceOf(BOB) == UNIT, "mint bob");
    }

    function testTransferOneWholeToken() public {
        token.mint(ALICE, 2 * UNIT);
        vm.expectEmit(true, true, false, true);
        emit Transfer(ALICE, BOB, UNIT);
        vm.prank(ALICE);
        require(IERC20(address(token)).transfer(BOB, UNIT), "return true");
        require(token.balanceOf(ALICE) == UNIT, "sender balance");
        require(token.balanceOf(BOB) == UNIT, "recipient balance");
        require(token.totalSupply() == 2 * UNIT, "supply preserved");
    }

    function testInsufficientBalanceReverts() public {
        token.mint(ALICE, UNIT);
        vm.expectRevert(abi.encodeWithSelector(LabToken.InsufficientBalance.selector, ALICE, UNIT, UNIT + 1));
        vm.prank(ALICE);
        token.transfer(BOB, UNIT + 1);
        require(token.balanceOf(ALICE) == UNIT && token.balanceOf(BOB) == 0, "atomic transfer");
    }

    function testUnauthorizedMintReverts() public {
        vm.expectRevert(abi.encodeWithSelector(LabToken.Unauthorized.selector, ALICE));
        vm.prank(ALICE);
        token.mint(ALICE, UNIT);
        require(token.totalSupply() == 0, "unauthorized supply");
    }

    function testZeroValueTransferEvent() public {
        vm.expectEmit(true, true, false, true);
        emit Transfer(ALICE, BOB, 0);
        vm.prank(ALICE);
        require(token.transfer(BOB, 0), "zero transfer");
    }

    function testSelfTransfer() public {
        token.mint(ALICE, UNIT);
        vm.prank(ALICE);
        token.transfer(ALICE, UNIT);
        require(token.balanceOf(ALICE) == UNIT, "self transfer balance");
    }

    function testApproveOverwriteAndTransferFrom() public {
        token.mint(ALICE, 3 * UNIT);
        vm.prank(ALICE);
        token.approve(SPENDER, UNIT);
        vm.expectEmit(true, true, false, true);
        emit Approval(ALICE, SPENDER, 2 * UNIT);
        vm.prank(ALICE);
        require(token.approve(SPENDER, 2 * UNIT), "approve");
        require(token.allowance(ALICE, SPENDER) == 2 * UNIT, "overwrite");
        vm.expectEmit(true, true, false, true);
        emit Transfer(ALICE, BOB, UNIT);
        vm.prank(SPENDER);
        require(token.transferFrom(ALICE, BOB, UNIT), "transferFrom");
        require(token.allowance(ALICE, SPENDER) == UNIT, "allowance decremented");
        require(token.balanceOf(ALICE) == 2 * UNIT && token.balanceOf(BOB) == UNIT, "delegated balances");
    }

    function testInsufficientAllowanceReverts() public {
        token.mint(ALICE, UNIT);
        vm.expectRevert(abi.encodeWithSelector(LabToken.InsufficientAllowance.selector, SPENDER, 0, UNIT));
        vm.prank(SPENDER);
        token.transferFrom(ALICE, BOB, UNIT);
    }

    function testTransferFromFailurePreservesAllowance() public {
        vm.prank(ALICE);
        token.approve(SPENDER, UNIT);
        vm.expectRevert(abi.encodeWithSelector(LabToken.InsufficientBalance.selector, ALICE, 0, UNIT));
        vm.prank(SPENDER);
        token.transferFrom(ALICE, BOB, UNIT);
        require(token.allowance(ALICE, SPENDER) == UNIT, "allowance rollback");
    }

    function testInfiniteAllowance() public {
        token.mint(ALICE, UNIT);
        vm.prank(ALICE);
        token.approve(SPENDER, type(uint256).max);
        vm.prank(SPENDER);
        token.transferFrom(ALICE, BOB, UNIT);
        require(token.allowance(ALICE, SPENDER) == type(uint256).max, "infinite allowance");
    }

    function testZeroTransferFromWithoutAllowance() public {
        vm.prank(SPENDER);
        require(token.transferFrom(ALICE, BOB, 0), "zero transferFrom");
    }

    function testZeroAddressesRevert() public {
        vm.expectRevert(abi.encodeWithSelector(LabToken.InvalidAddress.selector));
        token.mint(address(0), UNIT);
        vm.expectRevert(abi.encodeWithSelector(LabToken.InvalidAddress.selector));
        token.transfer(address(0), 0);
        vm.expectRevert(abi.encodeWithSelector(LabToken.InvalidAddress.selector));
        token.approve(address(0), 0);
        vm.expectRevert(abi.encodeWithSelector(LabToken.InvalidAddress.selector));
        token.transferFrom(address(0), BOB, 0);
        vm.expectRevert(abi.encodeWithSelector(LabToken.InvalidAddress.selector));
        new LabToken("Lab", "LAB", address(0));
    }

    function testEmptyMetadataReverts() public {
        vm.expectRevert(abi.encodeWithSelector(LabToken.EmptyMetadata.selector));
        new LabToken("", "LAB", ALICE);
        vm.expectRevert(abi.encodeWithSelector(LabToken.EmptyMetadata.selector));
        new LabToken("Lab", "", ALICE);
    }

    function testMintOverflowReverts() public {
        token.mint(ALICE, type(uint256).max);
        vm.expectRevert(abi.encodeWithSignature("Panic(uint256)", 0x11));
        token.mint(BOB, 1);
        require(token.totalSupply() == type(uint256).max && token.balanceOf(BOB) == 0, "overflow rollback");
    }

    function testFuzzTransferPreservesSupply(uint128 minted, uint128 requested) public {
        uint256 amount = uint256(requested) % (uint256(minted) + 1);
        token.mint(ALICE, minted);
        vm.prank(ALICE);
        token.transfer(BOB, amount);
        require(token.balanceOf(ALICE) + token.balanceOf(BOB) == token.totalSupply(), "conservation");
        require(token.balanceOf(BOB) == amount, "fuzz recipient");
    }
}
