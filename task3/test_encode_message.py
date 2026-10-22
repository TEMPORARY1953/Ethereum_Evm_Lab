import unittest

from encode_message import build_message, decode_message, encode_message, validate_address, validate_tx_hash

ADDRESS = "0x" + "12" * 20  # Synthetic test fixture, not a user's address.
TX_HASH = "0x" + "ab" * 32  # Synthetic test fixture, not a real transaction.


class EncodingTests(unittest.TestCase):
    def test_known_bytes(self):
        self.assertEqual(encode_message("Hello"), "0x48656c6c6f")
        self.assertEqual(encode_message("Иван"), "0xd098d0b2d0b0d0bd")

    def test_round_trip(self):
        for text in ("", "Alice", "Иван 👋", "line 1\nline 2"):
            with self.subTest(text=text):
                self.assertEqual(decode_message(encode_message(text)), text)

    def test_fields(self):
        message = build_message(" Иван ", ADDRESS, TX_HASH)
        self.assertEqual(message, f"Name: Иван\nEthereum address: {ADDRESS}\nTask 2 transaction hash: {TX_HASH}")
        self.assertEqual(decode_message(encode_message(message)), message)

    def test_bad_addresses(self):
        for address in ("<YOUR_ADDRESS>", "", "0x123", "0x" + "g" * 40, "0x" + "0" * 40, "12" * 20):
            with self.subTest(address=address), self.assertRaises(ValueError):
                validate_address(address)

    def test_bad_hashes(self):
        for tx_hash in ("<TASK2_TX_HASH>", "", "0x123", "0x" + "g" * 64, "0x" + "0" * 64, "ab" * 32):
            with self.subTest(tx_hash=tx_hash), self.assertRaises(ValueError):
                validate_tx_hash(tx_hash)

    def test_bad_names(self):
        for name in ("", "  ", "Alice\nInjected", "Alice\x00", "Alice\x7f"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                build_message(name, ADDRESS, TX_HASH)

    def test_bad_hex(self):
        for data in ("1234", "0x1", "0xgg", "0x12 34", "0x00\n"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                decode_message(data)

    def test_invalid_utf8(self):
        with self.assertRaises(UnicodeDecodeError):
            decode_message("0xff")

    def test_valid_syntax(self):
        self.assertEqual(validate_address(ADDRESS), ADDRESS)
        self.assertEqual(validate_tx_hash(TX_HASH), TX_HASH)


if __name__ == "__main__":
    unittest.main()
