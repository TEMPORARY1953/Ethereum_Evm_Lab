"""LOCAL ANVIL ONLY. Never contacts a public RPC or writes the real report.

The isolated chain uses Sepolia's ID to exercise the production chain checks.
All receipts/state live in a temporary directory and are discarded.
"""
import copy
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from unittest.mock import patch

import sepolia_metamask as app


def main():
    plan = app.load_plan()
    with tempfile.TemporaryDirectory(prefix="task4-local-test-") as temporary:
        folder = Path(temporary)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        process = subprocess.Popen([str(app.ROOT / ".tools/bin/anvil.exe"), "--silent",
                                    "--host", "127.0.0.1", "--port", str(port),
                                    "--chain-id", "11155111", "--hardfork", "cancun", "--base-fee", "0", "--no-mining"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            for _ in range(50):
                with socket.socket() as sock:
                    if sock.connect_ex(("127.0.0.1", port)) == 0:
                        break
                if process.poll() is not None:
                    raise RuntimeError("Isolated Anvil failed to start")
                time.sleep(0.1)
            else:
                raise RuntimeError("Isolated Anvil did not become ready")
            def local(method, params):
                assert url.startswith("http://127.0.0.1:")
                return json.loads(app.run("cast", "rpc", method, json.dumps(params),
                                          "--raw", "--rpc-url", url))
            local("anvil_impersonateAccount", [app.OWNER])
            local("anvil_setBalance", [app.OWNER, hex(10**20)])
            rpc = app.FoundryRpc(url)
            isolated_plan = folder / "plan.json"
            isolated_state = folder / "state.json"
            app.write_json(isolated_plan, plan)
            with patch.object(app, "PLAN", isolated_plan), patch.object(app, "STATE", isolated_state), \
                    patch.object(app, "update_report") as report:
                for step in app.STEPS:
                    review = app.preview(rpc, step)
                    assert review["decoded"]["ETH Value"] == "0 ETH"
                    assert review["decoded"]["symbol"] == "VMKRULIT"
                    reservation = app.reserve(rpc, step)
                    # A second tab/reload cannot reserve the same operation again.
                    try:
                        app.reserve(rpc, step)
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("Duplicate reservation accepted")
                    # Only a matching known rejection may release the reservation.
                    try:
                        app.release(step, "wrong-request-id")
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("Wrong reservation ID released the operation")
                    app.release(step, reservation["requestId"])
                    app.reserve(rpc, step)
                    state = app.load_state()
                    data = plan["creationData"] if step == "deploy" else plan[step + "Data"]
                    args = ["send", "--async", "--unlocked", "--from", app.OWNER,
                            "--rpc-url", url, "--gas-limit", str(app.GAS[step])]
                    args += ["--create", data] if step == "deploy" else [state["contract"], "--data", data]
                    tx_hash = app.run("cast", *args)
                    state["transactions"][step]["hash"] = tx_hash
                    app.write_json(isolated_state, state)
                    local("anvil_mine", ["0x2"])
                    state = app.verify_all(rpc)
                    assert state["transactions"][step]["evidence"]["confirmations"] >= 2
                assert state["status"] == "VERIFIED SEPOLIA SUCCESS"
                assert state["token"]["recipientBalance"] == str(app.AMOUNT)
                report.assert_called_once()
                # Incorrect calldata/recipient must not be accepted, even with a real receipt.
                incorrect = copy.deepcopy(plan)
                incorrect["transferData"] = plan["mintData"]
                try:
                    app.verify_step(rpc, incorrect, state, "transfer", state["transactions"]["transfer"]["hash"])
                except ValueError:
                    pass
                else:
                    raise AssertionError("Incorrect calldata accepted")
                # The backend's RPC wrapper must reject broadcasts.
                try:
                    rpc.call("eth_sendTransaction", [])
                except ValueError:
                    pass
                else:
                    raise AssertionError("RPC broadcast was allowed")
            # Check report output only against a disposable report.
            (folder / "FINAL_REPORT.md").write_text("# Temporary LOCAL test report\n\n| 4 | Pending |\n", encoding="utf-8")
            with patch.object(app, "ROOT", folder):
                app.update_report(plan, state)
                app.update_report(plan, state)
            report_text = (folder / "FINAL_REPORT.md").read_text(encoding="utf-8")
            assert report_text.count("<!-- SEPOLIA_TASK4_START -->") == 1
            assert state["contract"] in report_text
            print("PASS LOCAL ANVIL ONLY: deploy/mint/transfer, runtime + owner, metadata, balances,")
            print("canonical receipts, 2 confirmations, calldata rejection, read-only RPC, idempotent report.")
            print("PASS preview fees/decoded parameters, persistent cross-tab reservation, release ownership, mint balance at receipt block.")
            print("No public transaction sent. No local hashes written into FINAL_REPORT.md.")
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
