"""Offline UTF-8 message encoder. No wallet, RPC, or external dependencies."""
import argparse
import re


def validate_address(value: str) -> str:
    """Validate a 20-byte hex address (syntax, not EIP-55 checksum or ownership)."""
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", value):
        raise ValueError("Ethereum address must be 0x followed by 40 hex characters")
    if int(value[2:], 16) == 0:
        raise ValueError("Sender address must not be zero")
    return value


def validate_tx_hash(value: str) -> str:
    if not re.fullmatch(r"0x[0-9a-fA-F]{64}", value):
        raise ValueError("Transaction hash must be 0x followed by 64 hex characters")
    if int(value[2:], 16) == 0:
        raise ValueError("Transaction hash must not be zero")
    return value


def build_message(name: str, address: str, tx_hash: str) -> str:
    name = name.strip()
    if not name or any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise ValueError("Name must be nonempty and contain no control characters")
    return (f"Name: {name}\nEthereum address: {validate_address(address)}\n"
            f"Task 2 transaction hash: {validate_tx_hash(tx_hash)}")


def encode_message(message: str) -> str:
    return "0x" + message.encode("utf-8").hex()


def decode_message(hex_data: str) -> str:
    if not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*", hex_data):
        raise ValueError("Data must have 0x prefix and an even number of hex characters")
    return bytes.fromhex(hex_data[2:]).decode("utf-8", errors="strict")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name")
    parser.add_argument("--address")
    parser.add_argument("--tx-hash")
    parser.add_argument("--decode", metavar="HEX")
    args = parser.parse_args()
    try:
        if args.decode is not None:
            if any((args.name, args.address, args.tx_hash)):
                parser.error("--decode cannot be combined with message fields")
            print(decode_message(args.decode))
        else:
            if any(value is None for value in (args.name, args.address, args.tx_hash)):
                parser.error("Provide --name, --address and --tx-hash; replace placeholders with your data")
            print(encode_message(build_message(args.name, args.address, args.tx_hash)))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
