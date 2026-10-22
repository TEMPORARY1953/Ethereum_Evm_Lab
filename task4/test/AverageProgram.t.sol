// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

interface VmAverage {
    function etch(address target, bytes calldata code) external;
    function readFileBinary(string calldata path) external view returns (bytes memory);
}

/// @notice Full EVM cross-check of Task 1 once Foundry is available.
contract AverageProgramTest {
    VmAverage private constant vm = VmAverage(address(uint160(uint256(keccak256("hevm cheat code")))));
    address private constant PROGRAM = address(0x1337);

    function setUp() public {
        bytes memory code = vm.readFileBinary("../task1/program.bin");
        require(code.length == 139, "program length");
        vm.etch(PROGRAM, code);
    }

    function assertResult(bytes memory input, int256 expected) private view {
        (bool ok, bytes memory output) = PROGRAM.staticcall(input);
        require(ok && output.length == 32, "expected RETURN word");
        require(abi.decode(output, (int256)) == expected, "incorrect average");
    }

    function assertRevert(bytes memory input) private view {
        (bool ok, bytes memory output) = PROGRAM.staticcall(input);
        require(!ok && output.length == 0, "expected empty REVERT");
    }

    function testSingleAndZero() public view {
        assertResult(abi.encode(int256(1), int256(42)), 42);
        assertResult(abi.encode(int256(1), int256(-42)), -42);
        assertResult(abi.encode(int256(1), int256(0)), 0);
    }

    function testPositiveNegativeMixedAndFractions() public view {
        assertResult(abi.encode(int256(3), int256(10), int256(20), int256(30)), 20);
        assertResult(abi.encode(int256(3), int256(-3), int256(-6), int256(-9)), -6);
        assertResult(abi.encode(int256(3), int256(-10), int256(0), int256(19)), 3);
        assertResult(abi.encode(int256(3), int256(0), int256(0), int256(0)), 0);
        assertResult(abi.encode(int256(2), int256(1), int256(2)), 1);
        assertResult(abi.encode(int256(2), int256(-1), int256(-2)), -1);
        assertResult(abi.encode(int256(2), int256(-1), int256(0)), 0);
    }

    function testBadInputs() public view {
        assertRevert(hex"");
        assertRevert(hex"01");
        assertRevert(abi.encode(int256(0)));
        assertRevert(abi.encode(int256(-1), int256(1)));
        assertRevert(abi.encode(int256(1)));
        assertRevert(abi.encode(int256(2), int256(1)));
        assertRevert(abi.encode(int256(1), int256(1), int256(2)));
        assertRevert(bytes.concat(abi.encode(int256(1), int256(1)), hex"00"));
        assertRevert(abi.encode(int256(type(int256).max), int256(1)));
        assertRevert(abi.encode(uint256(1) << 251, int256(1)));
    }

    function testBoundariesAndOverflow() public view {
        assertResult(abi.encode(int256(1), type(int256).max), type(int256).max);
        assertResult(abi.encode(int256(1), type(int256).min), type(int256).min);
        assertResult(abi.encode(int256(2), type(int256).min, type(int256).max), 0);
        assertRevert(abi.encode(int256(2), type(int256).max, int256(1)));
        assertRevert(abi.encode(int256(2), type(int256).min, int256(-1)));
        assertRevert(abi.encode(int256(3), type(int256).max, int256(1), int256(-1)));
    }

    function testFuzzAverage(int128 a, int128 b, int128 c) public view {
        int256 expected = (int256(a) + int256(b) + int256(c)) / 3;
        assertResult(abi.encode(int256(3), int256(a), int256(b), int256(c)), expected);
    }
}
