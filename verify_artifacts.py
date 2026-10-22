"""Offline consistency checks; not a Solidity compiler or an ERC20 audit."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "task1"))
from local_evm import load_program, word  # noqa: E402
from test_program import cases  # noqa: E402

required = ["README.md", "FINAL_REPORT.md", "task1/program.evm", "task1/README.md", "task1/test_cases.md",
            "task2/README.md", "task2/report_template.md", "task3/encode_message.py", "task3/README.md",
            "task4/src/LabToken.sol", "task4/src/IERC20.sol", "task4/foundry.toml",
            "task4/test/LabToken.t.sol", "task4/script/Deploy.s.sol", "task4/scripts/local_demo.ps1", "task4/README.md",
            "task1/program.bin", ".tools/install.ps1", "run_local.ps1"]
for file in required:
    assert (ROOT / file).is_file(), f"Missing {file}"
program = load_program()  # Strict mnemonic-only assembler.
assert (ROOT / "task1/program.hex").read_text().strip() == "0x" + program.hex()
assert (ROOT / "task1/program.bin").read_bytes() == program
vectors = json.loads((ROOT / "task1/test_vectors.json").read_text())
assert len(vectors) == len(cases()) == 29
for vector, (name, data, expected) in zip(vectors, cases()):
    assert vector["name"] == name
    assert vector["calldata"] == "0x" + data.hex()
    assert vector["expected_int"] == expected
    assert vector["expected_status"] == ("revert" if expected is None else "return")
    assert vector["expected_hex"] == ("0x" if expected is None else "0x" + word(expected).hex())
for file in ROOT.rglob("*.sol"):
    if not file.is_file():
        continue  # Foundry also creates directories named Deploy.s.sol under broadcast/cache.
    for line in file.read_text(encoding="utf-8").splitlines():
        if line.startswith("import "):
            relative = line.split('"')[1]
            assert (file.parent / relative).is_file(), f"Missing Solidity import {relative}"
print(f"PASS: {len(required)} required artifacts, plain EVM mnemonics, bytecode, 29 vectors, local Solidity imports")
print("NOTE: Solidity compilation/ABI/runtime checks require real Foundry and solc")
