import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_zero_encodes_as_zero(self):
        self.assertEqual(encode(0), "0")

    def test_round_trip_includes_alphabet_boundaries(self):
        for number in (1, 9, 10, 35, 36, 61, 62, 63, 3843, 3844, 2**128):
            with self.subTest(number=number):
                self.assertEqual(decode(encode(number)), number)

    def test_decode_uses_digits_lowercase_then_uppercase(self):
        self.assertEqual(decode("0aAz"), 10 * 62**2 + 36 * 62 + 35)

    def test_encode_rejects_negative_and_non_integer_values(self):
        with self.assertRaises(ValueError):
            encode(-1)
        with self.assertRaises(TypeError):
            encode(True)
        with self.assertRaises(TypeError):
            encode(1.5)

    def test_decode_rejects_empty_or_invalid_codes(self):
        for code in ("", "a?", "é"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    decode(code)

    def test_decode_rejects_non_string_values(self):
        with self.assertRaises(TypeError):
            decode(1)


if __name__ == "__main__":
    unittest.main()
