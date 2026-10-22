"""Foundry preparation, loopback MetaMask UI and read-only Sepolia verification.

Python never signs or broadcasts. Only the user's browser calls eth_sendTransaction.
Run --prepare first; --serve remains locked unless --approved is explicitly supplied.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "task4"
sys.path.insert(0, str(ROOT / "task2"))
from sepolia_rpc import Rpc, receipt_evidence

OWNER = "0xfCB373793743A9bce32394EED450CEdfa7B10655"
RECIPIENT = "0x4a097d48ef380b479773eb609511a49cf17020f4"
TASK3 = "0xe0e9be26f386c5c1b6ccad6408b0af754c33b8c5937d21dc9700aecefb86532f"
RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
PLAN = TASK / "sepolia_plan.json"
STATE = TASK / "sepolia_result.json"
STEPS = ("deploy", "mint", "transfer")
AMOUNT = 10**18
TOKEN_NAME = "Vmk Rulit Token"
TOKEN_SYMBOL = "VMKRULIT"
MAX_FEE = 1_000_000_000
PRIORITY = 1_000_000
GAS = {"deploy": 4_500_000, "mint": 500_000, "transfer": 500_000}
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
RPC_READ_METHODS = {"eth_chainId", "eth_getBalance", "eth_estimateGas", "eth_getBlockByNumber",
                    "eth_getTransactionReceipt", "eth_getTransactionByHash", "eth_blockNumber",
                    "eth_getCode", "eth_call"}


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run(tool, *args, env=None):
    process = subprocess.run([str(ROOT / ".tools" / "bin" / (tool + ".exe")), *args],
                             cwd=TASK, env=env, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=180)
    if process.returncode:
        raise RuntimeError(process.stdout + process.stderr)
    return process.stdout.strip()


class FoundryRpc(Rpc):
    """Use the working Foundry HTTP transport, retaining the read-only allowlist."""
    def call(self, method, params):
        if method not in RPC_READ_METHODS:
            raise ValueError("Only read-only RPC methods are allowed")
        return json.loads(run("cast", "rpc", method, json.dumps(params), "--raw",
                              "--rpc-url", self.url, "--rpc-timeout", "20"))


def source_digest():
    paths = [TASK / "src/IERC20.sol", TASK / "src/LabToken.sol", TASK / "foundry.toml",
             TASK / "script/Deploy.s.sol"]
    return hashlib.sha256(b"".join(p.read_bytes() for p in paths)).hexdigest()


def prepare(rpc):
    if STATE.exists() and read_json(STATE).get("transactions"):
        raise ValueError("Existing transaction state: recover it before preparing another deployment")
    tests = run("forge", "test", "-vv")
    (ROOT / "checks/task4_final_foundry.log").write_text(tests + "\n", encoding="utf-8")
    run("forge", "build")
    artifact = read_json(TASK / "out/LabToken.sol/LabToken.json")
    encoded = run("cast", "abi-encode", "constructor(string,string,address)",
                  TOKEN_NAME, TOKEN_SYMBOL, OWNER)
    creation = artifact["bytecode"]["object"] + encoded[2:]
    rpc.guard()
    task3 = receipt_evidence(rpc, TASK3)
    if task3["status"] != "CONFIRMED SUCCESS" or task3["from"].lower() != OWNER.lower():
        raise ValueError("Task 3 receipt/sender mismatch")
    simulation_env = dict(os.environ, LAB_OWNER=OWNER, TOKEN_NAME=TOKEN_NAME, TOKEN_SYMBOL=TOKEN_SYMBOL)
    simulation = run("forge", "script", "script/Deploy.s.sol:Deploy", "--rpc-url", rpc.url,
                     "--sender", OWNER, env=simulation_env)  # Deliberately NO --broadcast.
    (ROOT / "checks/task4_sepolia_simulation.log").write_text(simulation + "\n", encoding="utf-8")
    estimate = int(rpc.call("eth_estimateGas", [{"from": OWNER, "data": creation, "value": "0x0",
                                               "gas": hex(GAS["deploy"])}]), 16)
    if estimate > GAS["deploy"]:
        raise ValueError(f"Deployment gas budget needs review: RPC estimate={estimate}, cap={GAS['deploy']}")
    balance = int(rpc.call("eth_getBalance", [OWNER, "latest"]), 16)
    budget = sum(GAS.values()) * MAX_FEE
    if balance < budget:
        raise ValueError(f"Need at least {budget} wei for the capped total gas budget; balance={balance}")
    plan = {"chainId": 11155111, "owner": OWNER, "recipient": RECIPIENT,
            "name": TOKEN_NAME, "symbol": TOKEN_SYMBOL, "amountBaseUnits": str(AMOUNT),
            "sourceSha256": source_digest(), "creationData": creation,
            "mintData": run("cast", "calldata", "mint(address,uint256)", OWNER, str(AMOUNT)),
            "transferData": run("cast", "calldata", "transfer(address,uint256)", RECIPIENT, str(AMOUNT)),
            "runtime": artifact["deployedBytecode"]["object"],
            "immutableReferences": artifact["deployedBytecode"]["immutableReferences"],
            "gasLimits": GAS, "maxFeePerGasWei": str(MAX_FEE),
            "maxPriorityFeePerGasWei": str(PRIORITY), "maxTotalFeeWei": str(budget),
            "deploymentGasEstimate": estimate, "senderBalanceWei": str(balance),
            "preparedAt": datetime.now(timezone.utc).isoformat(), "task3": task3}
    plan["planId"] = plan_digest(plan)
    write_json(PLAN, plan)
    print(json.dumps({k: plan[k] for k in ("chainId", "owner", "recipient", "deploymentGasEstimate",
                     "senderBalanceWei", "maxTotalFeeWei", "sourceSha256")}, indent=2))


def load_plan():
    plan = read_json(PLAN)
    if plan["sourceSha256"] != source_digest():
        raise ValueError("Sources changed; prepare and review the deployment again")
    if plan.get("planId") != plan_digest(plan):
        raise ValueError("Plan integrity check failed")
    if (plan["name"], plan["symbol"], plan["owner"], plan["recipient"], plan["chainId"],
            plan["amountBaseUnits"], plan["gasLimits"], plan["maxFeePerGasWei"], plan["maxPriorityFeePerGasWei"]) != (
            TOKEN_NAME, TOKEN_SYMBOL, OWNER, RECIPIENT, 11155111, str(AMOUNT), GAS, str(MAX_FEE), str(PRIORITY)):
        raise ValueError("Plan does not match the approved transaction parameters")
    return plan


def plan_digest(plan):
    keys = ("chainId", "owner", "recipient", "name", "symbol", "amountBaseUnits", "sourceSha256",
            "creationData", "mintData", "transferData", "runtime", "immutableReferences",
            "gasLimits", "maxFeePerGasWei", "maxPriorityFeePerGasWei")
    return hashlib.sha256(json.dumps({k: plan[k] for k in keys}, sort_keys=True).encode()).hexdigest()


def load_state():
    plan = load_plan()
    state = read_json(STATE) if STATE.exists() else {"chainId": 11155111, "planId": plan["planId"], "transactions": {}}
    if state.get("planId") != plan["planId"]:
        raise ValueError("Stored state belongs to a different deployment plan")
    return state


def runtime_check(rpc, plan, token):
    expected = bytearray.fromhex(plan["runtime"].removeprefix("0x"))
    for references in plan["immutableReferences"].values():
        for reference in references:
            start, size = reference["start"], reference["length"]
            expected[start:start + size] = bytes.fromhex(OWNER[2:]).rjust(size, b"\0")
    if rpc.call("eth_getCode", [token, "latest"]).lower() != "0x" + expected.hex():
        raise ValueError("On-chain runtime does not match the compiled LabToken + immutable owner")


def snapshot(rpc, token, block=None):
    block = block or rpc.call("eth_blockNumber", [])
    def call(data):
        return rpc.call("eth_call", [{"to": token, "data": data}, block])
    def string(data):
        raw = bytes.fromhex(call(data)[2:])
        offset = int.from_bytes(raw[:32], "big")
        length = int.from_bytes(raw[offset:offset + 32], "big")
        return raw[offset + 32:offset + 32 + length].decode("utf-8")
    values = {"block": int(block, 16), "owner": "0x" + call("0x8da5cb5b")[-40:],
              "name": string("0x06fdde03"), "symbol": string("0x95d89b41"),
              "decimals": int(call("0x313ce567"), 16),
              "totalSupply": str(int(call("0x18160ddd"), 16)),
              "ownerBalance": str(int(call("0x70a08231" + OWNER[2:].lower().zfill(64)), 16)),
              "recipientBalance": str(int(call("0x70a08231" + RECIPIENT[2:].zfill(64)), 16))}
    if (values["owner"].lower(), values["name"], values["symbol"], values["decimals"]) != (
            OWNER.lower(), TOKEN_NAME, TOKEN_SYMBOL, 18):
        raise ValueError("Token metadata mismatch")
    return values


def verify_step(rpc, plan, state, step, tx_hash):
    result = receipt_evidence(rpc, tx_hash)
    if result["status"] == "NOT MINED OR UNKNOWN":
        return result
    if result["status"] != "CONFIRMED SUCCESS":
        raise ValueError("Transaction failed or is not canonical; do not resend automatically")
    transaction = rpc.call("eth_getTransactionByHash", [tx_hash])
    token = state.get("contract")
    target = None if step == "deploy" else token
    data = plan["creationData"] if step == "deploy" else plan[step + "Data"]
    if (transaction["from"].lower() != OWNER.lower()
            or (transaction.get("to") or "").lower() != (target or "").lower()
            or transaction["input"].lower() != data.lower() or int(transaction["value"], 16) != 0
            or int(transaction["chainId"], 16) != 11155111):
        raise ValueError("Transaction sender/target/calldata/value/chain mismatch")
    if step == "deploy":
        token = result["contract_address"]
        if not token:
            raise ValueError("Deployment receipt has no contract address")
        runtime_check(rpc, plan, token)
        snapshot(rpc, token)
        state["contract"] = token
    else:
        sender = "0" * 64 if step == "mint" else OWNER[2:].lower().zfill(64)
        recipient = OWNER if step == "mint" else RECIPIENT
        expected = [TRANSFER_TOPIC, "0x" + sender, "0x" + recipient[2:].lower().zfill(64)]
        if not any(log["address"].lower() == token.lower()
                   and [t.lower() for t in log["topics"]] == expected
                   and int(log["data"], 16) == AMOUNT for log in result["receipt"]["logs"]):
            raise ValueError("Expected Transfer event missing")
        result["tokenAtReceiptBlock"] = snapshot(rpc, token, result["receipt"]["blockNumber"])
        if step == "mint" and (int(result["tokenAtReceiptBlock"]["totalSupply"]) != AMOUNT
                               or int(result["tokenAtReceiptBlock"]["ownerBalance"]) != AMOUNT):
            raise ValueError("Mint succeeded but supply/owner balance at its block is incorrect")
    return result


def verify_all(rpc):
    rpc.guard()
    plan, state = load_plan(), load_state()
    for step in STEPS:
        item = state["transactions"].get(step)
        if not item or not item.get("hash"):
            break
        evidence = verify_step(rpc, plan, state, step, item["hash"])
        item["evidence"] = evidence
        write_json(STATE, state)
        if evidence.get("confirmations", 0) < 2:
            break
    completed = all(state["transactions"].get(s, {}).get("evidence", {}).get("confirmations", 0) >= 2
                    for s in STEPS)
    if completed:
        runtime_check(rpc, plan, state["contract"])
        state["token"] = snapshot(rpc, state["contract"])
        if (int(state["token"]["totalSupply"]) != AMOUNT
                or int(state["token"]["recipientBalance"]) < AMOUNT
                or int(state["token"]["ownerBalance"]) != 0):
            raise ValueError("Unexpected final supply/balances")
        state["verifiedAt"] = datetime.now(timezone.utc).isoformat()
        state["status"] = "VERIFIED SEPOLIA SUCCESS"
        write_json(STATE, state)
        update_report(plan, state)
    return state


def gate(state, step):
    if step not in STEPS:
        raise ValueError("Unknown operation")
    if state["transactions"].get(step):
        raise ValueError("Operation already reserved/sent; recover its existing hash")
    for previous in STEPS[:STEPS.index(step)]:
        if state["transactions"].get(previous, {}).get("evidence", {}).get("confirmations", 0) < 2:
            raise ValueError("Previous operation needs successful receipt and 2 confirmations")


def unsigned_transaction(plan, state, step):
    transaction = {"from": OWNER, "chainId": "0xaa36a7", "value": "0x0",
                   "data": plan["creationData"] if step == "deploy" else plan[step + "Data"],
                   "gas": hex(GAS[step]), "maxFeePerGas": hex(MAX_FEE),
                   "maxPriorityFeePerGas": hex(PRIORITY)}
    if step != "deploy":
        transaction["to"] = state["contract"]
    return transaction


def preview(rpc, step):
    plan, state = load_plan(), verify_all(rpc)
    gate(state, step)
    transaction = unsigned_transaction(plan, state, step)
    estimate = int(rpc.call("eth_estimateGas", [transaction]), 16)
    if estimate * 120 // 100 > GAS[step]:
        raise ValueError("Gas estimate exceeds approved budget including margin; fees will not be increased")
    block = rpc.call("eth_getBlockByNumber", ["latest", False])
    price = int(block["baseFeePerGas"], 16) + PRIORITY
    if price > MAX_FEE:
        raise ValueError("Current fee exceeds approved cap; wait, do not increase fees automatically")
    if int(rpc.call("eth_getBalance", [OWNER, "pending"]), 16) < GAS[step] * MAX_FEE:
        raise ValueError("Insufficient Sepolia ETH for the approved gas budget")
    decoded = {"network": "Ethereum Sepolia", "chainId": 11155111, "from": OWNER,
               "to": transaction.get("to", "CONTRACT CREATION"), "ETH Value": "0 ETH",
               "name": TOKEN_NAME, "symbol": TOKEN_SYMBOL, "decimals": 18,
               "operation": "constructor(string,string,address)" if step == "deploy" else step + "(address,uint256)"}
    if step != "deploy":
        decoded.update({"tokenRecipient": OWNER if step == "mint" else RECIPIENT,
                        "tokenAmount": "1 VMKRULIT", "amountBaseUnits": str(AMOUNT)})
    return {"step": step, "planId": plan["planId"], "transaction": transaction, "decoded": decoded,
            "gasEstimate": estimate, "estimatedFeeWei": str(estimate * price),
            "maximumFeeWei": str(GAS[step] * MAX_FEE), "estimatedAtBlock": int(block["number"], 16)}


def reserve(rpc, step):
    state = verify_all(rpc)
    gate(state, step)
    request_id = secrets.token_urlsafe(24)
    state["transactions"][step] = {"status": "AWAITING_METAMASK", "requestId": request_id,
                                    "reservedAt": datetime.now(timezone.utc).isoformat()}
    write_json(STATE, state)
    return {"requestId": request_id, "state": state}


def release(step, request_id):
    state = load_state()
    item = state["transactions"].get(step, {})
    if item.get("hash") or not request_id or item.get("requestId") != request_id:
        raise ValueError("Only the matching rejected wallet request can be released")
    del state["transactions"][step]
    write_json(STATE, state)
    return state


def update_report(plan, state):
    path = ROOT / "FINAL_REPORT.md"
    text = path.read_text(encoding="utf-8-sig")
    start, end = "<!-- SEPOLIA_TASK4_START -->", "<!-- SEPOLIA_TASK4_END -->"
    rows = []
    for step in STEPS:
        evidence = state["transactions"][step]["evidence"]
        rows.append(f"| {step} | `{evidence['tx_hash']}` | {evidence['block_number']} | "
                    f"[Success]({evidence['etherscan']}) |")
    section = (f"{start}\n## Task 4: подтверждённое выполнение в Ethereum Sepolia\n\n"
               f"Проверено через read-only RPC `{RPC_URL}`: {state['verifiedAt']}. Chain ID: **11155111**.\n\n"
               f"Контракт: **`{state['contract']}`** — [Sepolia Etherscan](https://sepolia.etherscan.io/address/{state['contract']}).\n\n"
               f"Владелец: `{OWNER}`. Токен: **Vmk Rulit Token / VMKRULIT**, decimals **18**.\n"
               f"Выпущено **1 VMKRULIT** (10^18 единиц), переведено **1 VMKRULIT** на `{RECIPIENT}`.\n\n"
               "| Операция | Transaction hash | Блок | Etherscan |\n| --- | --- | --- | --- |\n"
               + "\n".join(rows) + "\n\n"
               f"На блоке {state['token']['block']}: totalSupply = `{state['token']['totalSupply']}`, "
               f"balanceOf(получатель) = `{state['token']['recipientBalance']}`, "
               f"balanceOf(owner) = `{state['token']['ownerBalance']}`.\n"
               "Проверены status=1, канонические блоки, минимум 2 подтверждения, точные calldata, "
               "отправитель, сеть, нулевой ETH value, события mint/transfer и runtime bytecode с immutable owner.\n"
               "Подпись — существующий MetaMask, по отдельному подтверждению пользователя для каждой операции.\n"
               "Доказательства: `task4/sepolia_result.json`; Foundry: `checks/task4_final_foundry.log` (23 PASS).\n"
               f"Task 3 также подтверждён: [{TASK3}](https://sepolia.etherscan.io/tx/{TASK3}), "
               f"блок {plan['task3']['block_number']}, status=1.\n"
               f"SHA-256 исходников/конфига: `{plan['sourceSha256']}`.\n{end}")
    if start in text:
        text = text[:text.index(start)] + section + text[text.index(end) + len(end):]
    else:
        text += "\n\n" + section + "\n"
    path.write_text(text, encoding="utf-8")


def serve(rpc, port, approved):
    plan = load_plan()
    rpc.guard()
    origin = f"http://127.0.0.1:{port}"
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def respond(self, value, status=200, content_type="application/json"):
            body = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; form-action 'none'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def valid_host(self):
            return self.headers.get("Host") == f"127.0.0.1:{port}"

        def do_GET(self):
            if not self.valid_host():
                return self.respond({"error": "Invalid host"}, 403)
            files = {"/": ("sepolia_signer.html", "text/html"),
                     "/signer.js": ("sepolia_signer.js", "text/javascript"),
                     "/signer.css": ("sepolia_signer.css", "text/css")}
            if self.path in files:
                name, kind = files[self.path]
                return self.respond((Path(__file__).parent / name).read_bytes(), content_type=kind)
            if self.path == "/api/plan":
                return self.respond({**load_plan(), "approved": approved, "state": load_state()})
            self.respond({"error": "Not found"}, 404)

        def do_POST(self):
            if not self.valid_host() or self.headers.get("Origin") != origin:
                return self.respond({"error": "Same-origin localhost only"}, 403)
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 2048 or self.headers.get("Content-Type") != "application/json":
                    raise ValueError("Invalid JSON request")
                payload = json.loads(self.rfile.read(size))
                if self.path in ("/api/verify", "/api/preview", "/api/reserve", "/api/release", "/api/record"):
                    if payload.get("planId") != load_plan()["planId"]:
                        raise ValueError("Deployment plan changed; reload the page before continuing")
                if self.path == "/api/verify":
                    return self.respond(verify_all(rpc))
                if self.path in ("/api/preview", "/api/reserve", "/api/release"):
                    if not approved:
                        raise ValueError("Awaiting user approval")
                    step = payload["step"]
                    if step not in STEPS:
                        raise ValueError("Unknown step")
                    if self.path == "/api/preview":
                        return self.respond(preview(rpc, step))
                    if self.path == "/api/reserve":
                        return self.respond(reserve(rpc, step))
                    return self.respond(release(step, payload.get("requestId")))
                if self.path == "/api/record":
                    if not approved:
                        raise ValueError("Awaiting explicit user approval")
                    step, tx_hash = payload["step"], payload["hash"]
                    if step not in STEPS or not re.fullmatch(r"0x[0-9a-fA-F]{64}", tx_hash):
                        raise ValueError("Invalid step/hash")
                    state = load_state()
                    prior = state["transactions"].get(step)
                    if prior and prior.get("hash") and prior["hash"].lower() != tx_hash.lower():
                        raise ValueError("A hash is already recorded; inspect it before any replacement")
                    for preceding in STEPS[:STEPS.index(step)]:
                        if state["transactions"].get(preceding, {}).get("evidence", {}).get("confirmations", 0) < 2:
                            raise ValueError("Previous step must be confirmed first")
                    # Validate available transaction data BEFORE accepting recovery hashes.
                    transaction = rpc.call("eth_getTransactionByHash", [tx_hash])
                    if transaction is not None:
                        expected = unsigned_transaction(load_plan(), state, step)
                        if (transaction["from"].lower() != OWNER.lower()
                                or (transaction.get("to") or "").lower() != expected.get("to", "").lower()
                                or transaction["input"].lower() != expected["data"].lower()
                                or int(transaction["value"], 16) != 0):
                            raise ValueError("Recovery hash does not match this operation")
                    state["transactions"].setdefault(step, {})["hash"] = tx_hash
                    state["transactions"][step]["status"] = "HASH_RECORDED"
                    write_json(STATE, state)  # Persist even while the receipt is pending.
                    return self.respond(verify_all(rpc))
                self.respond({"error": "Not found"}, 404)
            except Exception as error:
                self.respond({"error": str(error)}, 400)

    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"{origin}/ — {'APPROVED: MetaMask confirmations required' if approved else 'LOCKED: no transaction requests'}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--serve", action="store_true")
    modes.add_argument("--verify", action="store_true")
    parser.add_argument("--approved", action="store_true", help="Only after the user explicitly approves this plan")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    rpc = FoundryRpc(RPC_URL)
    if args.prepare:
        prepare(rpc)
    elif args.verify:
        print(json.dumps(verify_all(rpc), indent=2, ensure_ascii=False))
    else:
        serve(rpc, args.port, args.approved)
