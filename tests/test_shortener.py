import unittest

from src.hash_table import HashTable
from src.shortener import Shortener


class ShortenerTests(unittest.TestCase):
    def setUp(self):
        self.shortener = Shortener(table_class=HashTable, capacity=7)

    def test_shortens_and_expands_urls(self):
        code = self.shortener.shorten("https://example.com/a?b=1")
        self.assertEqual(code, "1")
        self.assertEqual(
            self.shortener.expand(code), "https://example.com/a?b=1"
        )

    def test_same_url_reuses_code_and_different_urls_do_not(self):
        first = self.shortener.shorten("http://example.com/one")
        self.assertEqual(
            self.shortener.shorten("http://example.com/one"), first
        )
        self.assertNotEqual(
            self.shortener.shorten("http://example.com/two"), first
        )

    def test_rejects_invalid_urls(self):
        for url in (
            "",
            "example.com/path",
            "ftp://example.com/file",
            "https:///missing-host",
            "https://example.com/white space",
            "https://[invalid",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    self.shortener.shorten(url)

    def test_rejects_non_string_url_and_unknown_code(self):
        with self.assertRaises(TypeError):
            self.shortener.shorten(1)
        with self.assertRaises(KeyError):
            self.shortener.expand("unknown")


if __name__ == "__main__":
    unittest.main()
