"""Offline consistency check of final report and collected real RPC evidence."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "task4/scripts"))
import sepolia_metamask as app

evidence = app.read_json(ROOT / "checks/final_sepolia_audit.json")
report = (ROOT / "FINAL_REPORT.md").read_text(encoding="utf-8")
plan = app.load_plan()
artifact = app.read_json(ROOT / "task4/out/LabToken.sol/LabToken.json")
constructor = app.run("cast", "abi-encode", "constructor(string,string,address)",
                      app.TOKEN_NAME, app.TOKEN_SYMBOL, app.OWNER)
assert artifact["bytecode"]["object"] + constructor[2:] == plan["creationData"]
assert artifact["deployedBytecode"]["object"] == plan["runtime"]
assert artifact["deployedBytecode"]["immutableReferences"] == plan["immutableReferences"]
items = [evidence["task2"], evidence["task3"], *evidence["task4"]["transactions"].values()]
for item in items:
    for value in (item["tx_hash"], str(item["block_number"]), item["etherscan"]):
        assert value in report, value
assert evidence["task3Decoded"]["text"] in report
assert evidence["task4"]["contract"] in report
assert "Vmk Rulit Token" in report and "VMKRULIT" in report
assert report.count("<!-- SEPOLIA_TASK4_START -->") == 1
for relative, digest in evidence["contractsSha256Before"].items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
assert (ROOT / "task3/message.txt").read_text(encoding="utf-8") == evidence["task3Decoded"]["text"]
assert (ROOT / "task3/message.hex").read_text().strip() == evidence["task3"]["input_data"]
print("PASS: report contains all 5 real hashes, blocks and links; exact Task 3 payload; Task 4 contract/name/symbol;")
print("fresh Foundry artifact + constructor match the deployed creation data; contract source hashes unchanged.")
