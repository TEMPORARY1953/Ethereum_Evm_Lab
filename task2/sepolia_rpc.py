"""Read-only Sepolia RPC preflight and evidence collector. Never signs or sends."""
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task3"))
from encode_message import validate_address, validate_tx_hash  # noqa: E402

CHAIN_ID = 11155111
ALLOWED_METHODS = {"eth_chainId", "eth_getBalance", "eth_estimateGas", "eth_getBlockByNumber",
                   "eth_maxPriorityFeePerGas", "eth_gasPrice", "eth_getTransactionReceipt",
                   "eth_getTransactionByHash", "eth_blockNumber", "eth_getCode", "eth_call"}


class Rpc:
    def __init__(self, url):
        if not url.startswith(("https://", "http://127.0.0.1:", "http://localhost:")):
            raise ValueError("Use HTTPS RPC or local loopback")
        self.url = url

    def call(self, method, params):
        if method not in ALLOWED_METHODS:
            raise ValueError("Only explicitly allowed read-only RPC methods may be used")
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        request = Request(self.url, data=body, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=20) as response:
            result = json.load(response)
        if "error" in result:
            raise ValueError(f"RPC {method}: {result['error']}")
        if "result" not in result:
            raise ValueError("Invalid JSON-RPC response")
        return result["result"]

    def guard(self):
        chain_id = int(self.call("eth_chainId", []), 16)
        if chain_id != CHAIN_ID:
            raise ValueError(f"Refusing chain {chain_id}; Ethereum Sepolia {CHAIN_ID} required")


def preflight(rpc, sender, recipient, value_wei, data="0x"):
    validate_address(sender)
    if recipient is not None:
        validate_address(recipient)
    if value_wei < 0:
        raise ValueError("Negative ETH value")
    if not data.startswith("0x") or len(data) % 2 or any(c not in "0123456789abcdefABCDEF" for c in data[2:]):
        raise ValueError("Invalid hex calldata")
    if recipient is None and data == "0x":
        raise ValueError("Contract deployment requires creation bytecode")
    rpc.guard()
    transaction = {"from": sender, "value": hex(value_wei), "data": data}
    if recipient is not None:
        transaction["to"] = recipient
    gas_estimate = int(rpc.call("eth_estimateGas", [transaction]), 16)
    block = rpc.call("eth_getBlockByNumber", ["latest", False])
    base_fee = int(block["baseFeePerGas"], 16)
    try:
        priority = int(rpc.call("eth_maxPriorityFeePerGas", []), 16)
    except ValueError:
        priority = max(int(rpc.call("eth_gasPrice", []), 16) - base_fee, 1)
    max_fee = 2 * base_fee + priority
    gas_limit = (gas_estimate * 120 + 99) // 100
    balance = int(rpc.call("eth_getBalance", [sender, "pending"]), 16)
    budget = value_wei + gas_limit * max_fee
    return {"status": "ESTIMATE ONLY; NOT SENT; MANUAL USE ONLY", "chain_id": CHAIN_ID,
            "sender": sender, "recipient": recipient or "CONTRACT CREATION", "value_wei": str(value_wei),
            "data": data, "estimated_at_block": int(block["number"], 16), "gas_estimate": gas_estimate,
            "suggested_gas_limit": gas_limit, "suggested_max_fee_per_gas_wei": str(max_fee),
            "suggested_priority_fee_per_gas_wei": str(priority),
            "upper_fee_budget_wei": str(gas_limit * max_fee), "total_budget_wei": str(budget),
            "sender_balance_wei": str(balance), "balance_sufficient": balance >= budget,
            "recipient_has_code": bool(recipient and rpc.call("eth_getCode", [recipient, "latest"]) != "0x")}


def receipt_evidence(rpc, tx_hash):
    validate_tx_hash(tx_hash)
    rpc.guard()
    receipt = rpc.call("eth_getTransactionReceipt", [tx_hash])
    if receipt is None:
        return {"chain_id": CHAIN_ID, "tx_hash": tx_hash, "status": "NOT MINED OR UNKNOWN"}
    transaction = rpc.call("eth_getTransactionByHash", [tx_hash])
    if transaction is None:
        raise ValueError("Receipt exists but transaction is missing")
    if receipt["transactionHash"].lower() != tx_hash.lower() or transaction["hash"].lower() != tx_hash.lower():
        raise ValueError("RPC returned a different transaction")
    block = rpc.call("eth_getBlockByNumber", [receipt["blockNumber"], False])
    canonical = block is not None and block["hash"].lower() == receipt["blockHash"].lower()
    height = int(rpc.call("eth_blockNumber", []), 16)
    number = int(receipt["blockNumber"], 16)
    status = "CONFIRMED SUCCESS" if int(receipt["status"], 16) == 1 and canonical else "FAILED OR NONCANONICAL"
    return {"chain_id": CHAIN_ID, "status": status, "tx_hash": tx_hash, "block_number": number,
            "block_hash": receipt["blockHash"], "canonical": canonical, "confirmations": max(0, height - number + 1),
            "from": transaction["from"], "to": transaction["to"], "value_wei": str(int(transaction["value"], 16)),
            "input_data": transaction["input"], "contract_address": receipt.get("contractAddress"),
            "gas_used": int(receipt["gasUsed"], 16),
            "actual_fee_wei": str(int(receipt["gasUsed"], 16) * int(receipt["effectiveGasPrice"], 16)),
            "etherscan": f"https://sepolia.etherscan.io/tx/{tx_hash}", "receipt": receipt}


def token_balance(rpc, token, address):
    validate_address(token)
    validate_address(address)
    rpc.guard()
    if rpc.call("eth_getCode", [token, "latest"]) == "0x":
        raise ValueError("Token address has no code")
    height = rpc.call("eth_blockNumber", [])
    raw = rpc.call("eth_call", [{"to": token, "data": "0x70a08231" + address[2:].lower().zfill(64)}, height])
    decimals_raw = rpc.call("eth_call", [{"to": token, "data": "0x313ce567"}, height])
    if len(raw) != 66 or len(decimals_raw) != 66:
        raise ValueError("Malformed ABI return data")
    balance, decimals = int(raw, 16), int(decimals_raw, 16)
    if decimals > 255:
        raise ValueError("Malformed decimals")
    return {"chain_id": CHAIN_ID, "token": token, "address": address, "block_number": int(height, 16),
            "balance_base_units": str(balance), "decimals": decimals, "at_least_one_whole_token": balance >= 10**decimals}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc-url", required=True)
    parser.add_argument("--output", help="Save JSON inside project only")
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--sender", required=True)
    plan.add_argument("--recipient")
    plan.add_argument("--value-wei", type=int, required=True)
    plan.add_argument("--data", default="0x")
    receipt = commands.add_parser("receipt")
    receipt.add_argument("--tx-hash", required=True)
    balance = commands.add_parser("balance")
    balance.add_argument("--token", required=True)
    balance.add_argument("--address", required=True)
    args = parser.parse_args()
    try:
        rpc = Rpc(args.rpc_url)
        if args.command == "plan":
            result = preflight(rpc, args.sender, args.recipient, args.value_wei, args.data)
        elif args.command == "receipt":
            result = receipt_evidence(rpc, args.tx_hash)
        else:
            result = token_balance(rpc, args.token, args.address)
        output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            project = Path(__file__).resolve().parents[1]
            target = Path(args.output).resolve()
            if not target.is_relative_to(project):
                raise ValueError("Output must stay inside the project")
            target.write_text(output, encoding="utf-8")
        print(output, end="")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        # Endpoint URLs can contain API credentials, so network exceptions are not echoed.
        if isinstance(exc, OSError):
            parser.exit(1, "RPC network access failed; check endpoint/connectivity. Nothing sent.\n")
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
