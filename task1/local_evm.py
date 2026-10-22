"""Restricted opcode interpreter for offline checks, NOT a complete Cancun EVM.

Executes the actual assembled bytes. No gas accounting, transactions or world state.
Operand order follows Ethereum execution-specs (top is popped first).
"""
from pathlib import Path
import re

MODULUS = 1 << 256
MASK = MODULUS - 1
MIN_INT = -(1 << 255)
MAX_INT = (1 << 255) - 1
OPCODES = {
    "ADD": 0x01, "SUB": 0x03, "DIV": 0x04, "SDIV": 0x05,
    "LT": 0x10, "SGT": 0x13, "EQ": 0x14, "ISZERO": 0x15,
    "AND": 0x16, "XOR": 0x18, "SHR": 0x1C,
    "CALLDATALOAD": 0x35, "CALLDATASIZE": 0x36,
    "MLOAD": 0x51, "MSTORE": 0x52, "JUMP": 0x56, "JUMPI": 0x57,
    "JUMPDEST": 0x5B, "PUSH0": 0x5F, "SWAP1": 0x90,
    "RETURN": 0xF3, "REVERT": 0xFD,
}


def signed(value):
    return value if value < (1 << 255) else value - MODULUS


def word(value):
    if not MIN_INT <= value <= MASK:
        raise ValueError("Value does not fit a 256-bit word")
    return (value & MASK).to_bytes(32, "big")


def calldata(n, values):
    return word(n) + b"".join(word(value) for value in values)


def assemble(text):
    code = bytearray()
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"PUSH([1-9]|[12][0-9]|3[0-2]) 0x([0-9a-fA-F]+)", line)
        if match:
            width = int(match[1])
            immediate = int(match[2], 16)
            if immediate >= 1 << (8 * width):
                raise ValueError("PUSH immediate exceeds its declared width")
            code.append(0x5F + width)
            code.extend(immediate.to_bytes(width, "big"))
        elif line in OPCODES:
            code.append(OPCODES[line])
        else:
            raise ValueError(f"Not a supported plain mnemonic: {line!r}")
    return bytes(code)


def execute(code, data, step_limit=200_000):
    stack, memory, destinations = [], bytearray(), set()
    cursor = 0
    while cursor < len(code):
        op = code[cursor]
        if op == 0x5B:
            destinations.add(cursor)
        cursor += 1 + (op - 0x5F if 0x60 <= op <= 0x7F else 0)

    def pop():
        if not stack:
            raise ValueError("Stack underflow")
        return stack.pop()

    def push(value):
        if len(stack) >= 1024:
            raise ValueError("Stack overflow")
        stack.append(value & MASK)

    def expand(end):
        if end > 4096:
            raise ValueError("Restricted interpreter memory limit exceeded")
        if end > len(memory):
            memory.extend(b"\0" * (end - len(memory)))

    pc, peak = 0, 0
    for _ in range(step_limit):
        op = code[pc]
        pc += 1
        if op == 0x5F:
            push(0)
        elif 0x60 <= op <= 0x7F:
            width = op - 0x5F
            if pc + width > len(code):
                raise ValueError("Truncated PUSH")
            push(int.from_bytes(code[pc:pc + width], "big"))
            pc += width
        elif op == 0x90:
            if len(stack) < 2:
                raise ValueError("SWAP underflow")
            stack[-1], stack[-2] = stack[-2], stack[-1]
        elif op == 0x35:
            offset = pop()
            push(int.from_bytes(data[offset:offset + 32].ljust(32, b"\0"), "big"))
        elif op == 0x36:
            push(len(data))
        elif op == 0x51:
            offset = pop()
            expand(offset + 32)
            push(int.from_bytes(memory[offset:offset + 32], "big"))
        elif op == 0x52:
            offset, value = pop(), pop()
            expand(offset + 32)
            memory[offset:offset + 32] = word(value)
        elif op == 0x15:
            push(int(pop() == 0))
        elif op in (0x01, 0x03, 0x04, 0x05, 0x10, 0x13, 0x14, 0x16, 0x18, 0x1C):
            a, b = pop(), pop()
            if op == 0x01:
                push(a + b)
            elif op == 0x03:
                push(a - b)
            elif op == 0x04:
                push(a // b if b else 0)
            elif op == 0x05:
                a, b = signed(a), signed(b)
                push(((-1 if (a < 0) != (b < 0) else 1) * (abs(a) // abs(b))) if b else 0)
            elif op == 0x10:
                push(int(a < b))
            elif op == 0x13:
                push(int(signed(a) > signed(b)))
            elif op == 0x14:
                push(int(a == b))
            elif op == 0x16:
                push(a & b)
            elif op == 0x18:
                push(a ^ b)
            else:
                push(b >> a if a < 256 else 0)
        elif op in (0x56, 0x57):
            target = pop()
            should_jump = op == 0x56 or pop() != 0
            if should_jump:
                if target not in destinations:
                    raise ValueError(f"Invalid jump target: {target}")
                pc = target
        elif op == 0x5B:
            # All block boundaries of this particular program must have empty stack.
            if stack:
                raise ValueError("Temporary values leaked across a basic block")
        elif op in (0xF3, 0xFD):
            offset, size = pop(), pop()
            expand(offset + size)
            return {"status": "return" if op == 0xF3 else "revert",
                    "data": bytes(memory[offset:offset + size]), "stack": stack.copy(),
                    "max_stack": peak}
        else:
            raise ValueError(f"Unsupported opcode: {op:#x}")
        peak = max(peak, len(stack))
        if not 0 <= pc < len(code):
            raise ValueError("Unexpected end of program")
    raise ValueError("Step limit exceeded")


def load_program():
    return assemble(Path(__file__).with_name("program.evm").read_text(encoding="utf-8"))
