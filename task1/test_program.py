import argparse
import json
from pathlib import Path
import random
import unittest

from local_evm import MAX_INT, MIN_INT, assemble, calldata, execute, load_program, signed, word


def cases():
    return [
        ("N=1", calldata(1, [42]), 42),
        ("positive numbers", calldata(3, [10, 20, 30]), 20),
        ("negative numbers", calldata(3, [-3, -6, -9]), -6),
        ("mixed signs", calldata(3, [-10, 0, 19]), 3),
        ("zero elements", calldata(3, [0, 0, 0]), 0),
        ("positive fractional average", calldata(2, [1, 2]), 1),
        ("negative fractional average", calldata(2, [-1, -2]), -1),
        ("fraction rounded to zero", calldata(2, [-1, 0]), 0),
        ("negative N=1", calldata(1, [-42]), -42),
        ("N=1 zero", calldata(1, [0]), 0),
        ("N=0", calldata(0, []), None),
        ("N=0 with extra value", calldata(0, [5]), None),
        ("negative N", calldata(-1, [5]), None),
        ("missing word", calldata(2, [10]), None),
        ("extra word", calldata(1, [10, 20]), None),
        ("empty input", b"", None),
        ("N without values", calldata(1, []), None),
        ("truncated N", b"\x01", None),
        ("truncated element", calldata(1, [42])[:-1], None),
        ("extra byte", calldata(1, [42]) + b"\x00", None),
        ("huge positive N", calldata(MAX_INT, [1]), None),
        ("N multiplication wrap attack", calldata(1 << 251, [1]), None),
        ("N sign bit", calldata(1 << 255, [1]), None),
        ("maximum int256", calldata(1, [MAX_INT]), MAX_INT),
        ("minimum int256", calldata(1, [MIN_INT]), MIN_INT),
        ("positive sum overflow", calldata(2, [MAX_INT, 1]), None),
        ("negative sum overflow", calldata(2, [MIN_INT, -1]), None),
        ("overflow before later cancellation", calldata(3, [MAX_INT, 1, -1]), None),
        ("extremes without overflow", calldata(2, [MIN_INT, MAX_INT]), 0),
    ]


class ProgramTests(unittest.TestCase):
    def check_result(self, data, expected):
        result = execute(load_program(), data)
        self.assertEqual(result["stack"], [], "stack must be empty at termination")
        self.assertLessEqual(result["max_stack"], 3)
        if expected is None:
            self.assertEqual(result["status"], "revert")
            self.assertEqual(result["data"], b"")
        else:
            self.assertEqual(result["status"], "return")
            self.assertEqual(result["data"], word(expected))

    def test_documented_cases(self):
        for name, data, expected in cases():
            with self.subTest(case=name):
                self.check_result(data, expected)

    def test_randomized_against_independent_integer_reference(self):
        rng = random.Random(20261022)
        edge = [MIN_INT, MIN_INT + 1, -1, 0, 1, MAX_INT - 1, MAX_INT]
        for _ in range(1000):
            values = [rng.choice(edge) if rng.randrange(3) == 0 else rng.randint(-10**20, 10**20)
                      for _ in range(rng.randint(1, 16))]
            running = 0
            expected = None
            for value in values:
                running += value
                if not MIN_INT <= running <= MAX_INT:
                    break
            else:
                expected = (-1 if running < 0 else 1) * (abs(running) // len(values))
            self.check_result(calldata(len(values), values), expected)

    def test_operand_order_reference(self):
        samples = [("PUSH1 0x02\nPUSH1 0x07\nSUB", 5),
                   ("PUSH1 0x02\nPUSH1 0x07\nDIV", 3),
                   ("PUSH1 0x07\nPUSH1 0x02\nLT", 1),
                   ("PUSH1 0x00\nPUSH1 0x02\nSGT", 1),
                   ("PUSH1 0x08\nPUSH1 0x02\nSHR", 2)]
        for prefix, expected in samples:
            code = assemble(prefix + "\nPUSH0\nMSTORE\nPUSH1 0x20\nPUSH0\nRETURN")
            self.assertEqual(signed(int.from_bytes(execute(code, b"")["data"], "big")), expected)

    def test_plain_mnemonics_and_jump_immediates(self):
        code = load_program()
        self.assertEqual(len(code), 139)
        for destination in (54, 122, 135):
            self.assertEqual(code[destination], 0x5B)
        with self.assertRaises(ValueError):
            assemble("loop:\nJUMPDEST")


def write_cases():
    root = Path(__file__).parent
    records = []
    lines = ["# Task 1: воспроизводимые тестовые примеры", "",
             "Все calldata полные, без selector и без ABI-смещения массива. Для успешного вызова",
             "ожидается ровно одно 32-байтовое слово. REVERT возвращает пустые данные.", "",
             "Локальные результаты относятся к ограниченному интерпретатору `local_evm.py`.",
             "Полноценная Cancun EVM / Playground в этой среде не запускалась.", ""]
    for name, data, expected in cases():
        record = {"name": name, "calldata": "0x" + data.hex(), "expected_status": "revert" if expected is None else "return",
                  "expected_int": expected, "expected_hex": "0x" if expected is None else "0x" + word(expected).hex()}
        records.append(record)
        lines.extend([f"## {name}", "", f"Ожидание: {'REVERT' if expected is None else expected}.", "",
                      "Calldata:", "", "```text", record["calldata"], "```", "",
                      "Return data:", "", "```text", record["expected_hex"], "```", ""])
    (root / "test_cases.md").write_text("\n".join(lines), encoding="utf-8")
    (root / "test_vectors.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    (root / "program.hex").write_text("0x" + load_program().hex() + "\n", encoding="utf-8")
    (root / "program.bin").write_bytes(load_program())
    print(f"Wrote {len(records)} vectors and assembled bytecode")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-cases", action="store_true")
    args, remaining = parser.parse_known_args()
    if args.write_cases:
        write_cases()
    else:
        unittest.main(argv=[__file__] + remaining)
