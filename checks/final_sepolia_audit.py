"""Read-only audit of existing Task 2-4 transactions. Never signs or broadcasts."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "task4/scripts"))
import sepolia_metamask as app
sys.path.insert(0, str(ROOT / "task3"))
from encode_message import build_message, encode_message, decode_message


def main():
    before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (ROOT / "task4/src").glob("*.sol")}
    rpc = app.FoundryRpc(app.RPC_URL)
    rpc.guard()
    task3 = app.receipt_evidence(rpc, app.TASK3)
    assert task3["status"] == "CONFIRMED SUCCESS" and task3["confirmations"] >= 2
    assert task3["from"].lower() == app.OWNER.lower()
    assert task3["to"].lower() == app.RECIPIENT.lower() and int(task3["value_wei"]) > 0
    message = decode_message(task3["input_data"])
    parsed = re.fullmatch(r"Name: ([^\r\n]+)\nEthereum address: (0x[0-9a-fA-F]{40})\nTask 2 transaction hash: (0x[0-9a-fA-F]{64})", message)
    assert parsed, "Task 3 payload does not match the required three fields"
    name, address, task2_hash = parsed.groups()
    assert address.lower() == app.OWNER.lower()
    assert encode_message(build_message(name, address, task2_hash)).lower() == task3["input_data"].lower()
    task2 = app.receipt_evidence(rpc, task2_hash)
    assert task2["status"] == "CONFIRMED SUCCESS" and task2["confirmations"] >= 2
    assert task2["from"].lower() == app.OWNER.lower() and int(task2["value_wei"]) > 0
    assert task2["block_number"] < task3["block_number"]
    plan = app.load_plan()
    state = copy.deepcopy(app.load_state())
    task4 = {}
    for step in app.STEPS:
        task4[step] = app.verify_step(rpc, plan, state, step, state["transactions"][step]["hash"])
        assert task4[step]["status"] == "CONFIRMED SUCCESS" and task4[step]["confirmations"] >= 2
    token = app.snapshot(rpc, state["contract"])
    app.runtime_check(rpc, plan, state["contract"])
    assert int(token["totalSupply"]) == app.AMOUNT
    assert int(token["recipientBalance"]) == app.AMOUNT and int(token["ownerBalance"]) == 0
    assert task4["deploy"]["block_number"] < task4["mint"]["block_number"] < task4["transfer"]["block_number"]
    after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (ROOT / "task4/src").glob("*.sol")}
    assert before == after
    evidence = {"verifiedAt": datetime.now(timezone.utc).isoformat(), "chainId": 11155111,
                "rpc": app.RPC_URL, "mode": "READ ONLY; NO TRANSACTIONS SENT",
                "task2": task2, "task3": task3,
                "task3Decoded": {"name": name, "address": address, "task2Hash": task2_hash, "text": message},
                "task4": {"contract": state["contract"], "transactions": task4, "token": token},
                "contractsSha256Before": before, "contractsSha256After": after}
    app.write_json(ROOT / "checks/final_sepolia_audit.json", evidence)
    # Save exact public evidence; these files are recovered from RPC, never newly sent.
    app.write_json(ROOT / "task2/receipt.json", task2)
    app.write_json(ROOT / "task3/receipt.json", task3)
    (ROOT / "task3/message.txt").write_text(message, encoding="utf-8")
    (ROOT / "task3/message.hex").write_text(task3["input_data"] + "\n", encoding="ascii")
    summary = {"verifiedAt": evidence["verifiedAt"], "chainId": 11155111, "readOnly": True,
               "task2": {k: task2[k] for k in ("tx_hash", "from", "to", "value_wei", "input_data", "block_number", "confirmations")},
               "task3": {k: task3[k] for k in ("tx_hash", "block_number", "value_wei", "confirmations")},
               "message": message, "token": {"contract": state["contract"], **token},
               "task4": {step: {k: item[k] for k in ("tx_hash", "block_number", "confirmations")} for step, item in task4.items()},
               "contractsUnchanged": before == after}
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
