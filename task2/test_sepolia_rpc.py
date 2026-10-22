import unittest
from sepolia_rpc import Rpc, preflight, receipt_evidence, token_balance

ADDRESS = "0x" + "12" * 20
RECIPIENT = "0x" + "34" * 20
TX = "0x" + "ab" * 32
BLOCK = "0x" + "cd" * 32


class FakeRpc:
    def __init__(self, chain=11155111):
        self.chain = chain
        self.methods = []

    def guard(self):
        Rpc.guard(self)

    def call(self, method, params):
        self.methods.append(method)
        values = {"eth_chainId": hex(self.chain), "eth_estimateGas": hex(21000),
                  "eth_getBlockByNumber": {"number": "0x64", "baseFeePerGas": hex(10**9), "hash": BLOCK},
                  "eth_maxPriorityFeePerGas": hex(10**8), "eth_getBalance": hex(10**18),
                  "eth_getCode": "0x", "eth_blockNumber": "0x65",
                  "eth_getTransactionReceipt": {"status": "0x1", "transactionHash": TX, "blockNumber": "0x64",
                    "blockHash": BLOCK, "gasUsed": hex(21000), "effectiveGasPrice": hex(10**9), "contractAddress": None},
                  "eth_getTransactionByHash": {"hash": TX, "from": ADDRESS, "to": RECIPIENT, "value": "0x1", "input": "0x"}}
        return values[method]


class RpcTests(unittest.TestCase):
    def test_plan_is_read_only(self):
        rpc = FakeRpc()
        result = preflight(rpc, ADDRESS, RECIPIENT, 10**13)
        self.assertEqual(result["chain_id"], 11155111)
        self.assertEqual(result["gas_estimate"], 21000)
        self.assertEqual(result["suggested_gas_limit"], 25200)
        self.assertTrue(result["balance_sufficient"])
        self.assertFalse(any("send" in method.lower() for method in rpc.methods))

    def test_mainnet_refused(self):
        with self.assertRaisesRegex(ValueError, "Refusing chain"):
            preflight(FakeRpc(chain=1), ADDRESS, RECIPIENT, 1)

    def test_invalid_data(self):
        for value, data in ((-1, "0x"), (1, "0x1"), (1, "bad")):
            with self.subTest(value=value, data=data), self.assertRaises(ValueError):
                preflight(FakeRpc(), ADDRESS, RECIPIENT, value, data)

    def test_receipt_and_confirmation(self):
        result = receipt_evidence(FakeRpc(), TX)
        self.assertEqual(result["status"], "CONFIRMED SUCCESS")
        self.assertEqual(result["block_number"], 100)
        self.assertEqual(result["confirmations"], 2)
        self.assertEqual(result["actual_fee_wei"], str(21000 * 10**9))

    def test_noncanonical_receipt(self):
        class ReorgRpc(FakeRpc):
            def call(self, method, params):
                result = super().call(method, params)
                if method == "eth_getBlockByNumber":
                    result["hash"] = "0x" + "ef" * 32
                return result
        self.assertEqual(receipt_evidence(ReorgRpc(), TX)["status"], "FAILED OR NONCANONICAL")

    def test_unknown_receipt(self):
        class PendingRpc(FakeRpc):
            def call(self, method, params):
                return None if method == "eth_getTransactionReceipt" else super().call(method, params)
        self.assertEqual(receipt_evidence(PendingRpc(), TX)["status"], "NOT MINED OR UNKNOWN")

    def test_rpc_send_method_blocked(self):
        rpc = Rpc("https://example.invalid")
        with self.assertRaisesRegex(ValueError, "read-only"):
            rpc.call("eth_sendRawTransaction", ["0x00"])

    def test_balance_read(self):
        class TokenRpc(FakeRpc):
            def call(self, method, params):
                if method == "eth_getCode":
                    return "0x6000"
                if method == "eth_call":
                    return "0x" + format(18 if params[0]["data"] == "0x313ce567" else 10**18, "064x")
                return super().call(method, params)
        result = token_balance(TokenRpc(), ADDRESS, RECIPIENT)
        self.assertEqual(result["balance_base_units"], str(10**18))
        self.assertTrue(result["at_least_one_whole_token"])


if __name__ == "__main__":
    unittest.main()
