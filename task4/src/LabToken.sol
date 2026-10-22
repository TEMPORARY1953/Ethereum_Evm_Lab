// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import {IERC20} from "./IERC20.sol";

/// @notice Self-contained educational ERC20 implementation; no external dependencies.
/// @dev Amounts, including mint amounts, are always expressed in base units.
contract LabToken is IERC20 {
    string public name;
    string public symbol;
    uint8 public constant decimals = 18;
    address public immutable owner;

    uint256 public override totalSupply;
    mapping(address => uint256) public override balanceOf;
    mapping(address => mapping(address => uint256)) public override allowance;

    error Unauthorized(address caller);
    error InvalidAddress();
    error EmptyMetadata();
    error InsufficientBalance(address account, uint256 balance, uint256 needed);
    error InsufficientAllowance(address spender, uint256 remaining, uint256 needed);

    constructor(string memory tokenName, string memory tokenSymbol, address tokenOwner) {
        if (tokenOwner == address(0)) revert InvalidAddress();
        if (bytes(tokenName).length == 0 || bytes(tokenSymbol).length == 0) revert EmptyMetadata();
        name = tokenName;
        symbol = tokenSymbol;
        owner = tokenOwner;
    }

    function mint(address to, uint256 value) external {
        if (msg.sender != owner) revert Unauthorized(msg.sender);
        if (to == address(0)) revert InvalidAddress();
        totalSupply += value;
        balanceOf[to] += value;
        emit Transfer(address(0), to, value);
    }

    function transfer(address to, uint256 value) external override returns (bool) {
        _transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) external override returns (bool) {
        if (spender == address(0)) revert InvalidAddress();
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external override returns (bool) {
        uint256 remaining = allowance[from][msg.sender];
        if (remaining != type(uint256).max) {
            if (remaining < value) revert InsufficientAllowance(msg.sender, remaining, value);
            allowance[from][msg.sender] = remaining - value;
        }
        _transfer(from, to, value);
        return true;
    }

    function _transfer(address from, address to, uint256 value) private {
        if (from == address(0) || to == address(0)) revert InvalidAddress();
        uint256 available = balanceOf[from];
        if (available < value) revert InsufficientBalance(from, available, value);
        balanceOf[from] = available - value;
        balanceOf[to] += value;
        emit Transfer(from, to, value);
    }
}
