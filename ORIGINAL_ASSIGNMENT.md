# Original assignment — supplied by the user

## Task 1

Write an EVM mnemonic-opcodes program (no Solidity/Yul) that:

- Reads from input calldata int N and N words (int numbers)
- Validates input: N > 0, N words are given
- Computes the average
- Clears the stack
- Returns the result

Use https://www.evm.codes/playground (cancun)

## Task 2

Install a browser extension Metamask for Chrome, Firefox, Opera, or Brave at your choice.
Create a new wallet, connect to the Sepolia test network (if you do not see Sepolia in
the Select networks list, go to Settings-Advanced-Show test networks in your Metamask).
Get some test ETH from a faucet. Find a colleague and send a test ETH transaction in
Sepolia test network, use Etherscan (https://sepolia.etherscan.io/) to locate the block
with your transaction.

## Task 3

Use your Metamask extension to send an onchain message with non zero value from your
new wallet to the 0x4A097D48ef380B479773EB609511a49CF17020f4 Ethereum address in Sepolia
test network. The message should include your name, your Ethereum address and the
test transaction hash from the previous point. NB: you’ll have to turn on
Settings-Advanced-Show Hex Data in your Metamask. The input has to be in Hex with the
0x prefix. An example of valid Hex input data for an onchain message:
0x48656c6c6f20776f726c6421.

## Task 4

Deploy ERC20 token using Foundry or Remix IDE on Sepolia testnet and change the name
and the symbol of the token to your own. Mint some tokens (at least 1 in notional
with decimals) and send them to the 0x4A097D48ef380B479773EB609511a49CF17020f4 Sepolia
address.
