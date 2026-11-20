import unittest

from src.hash_table import HashTable, LinearProbingHashTable
from src.shortener import Shortener


class ShortenerTests(unittest.TestCase):
    table_classes = (HashTable, LinearProbingHashTable)

    def test_shortens_and_expands_urls(self):
        for table_class in self.table_classes:
            with self.subTest(table=table_class.__name__):
                shortener = Shortener(table_class=table_class, capacity=7)
                code = shortener.shorten("https://example.com/a?b=1")
                self.assertEqual(code, "1")
                self.assertEqual(
                    shortener.expand(code), "https://example.com/a?b=1"
                )

    def test_same_url_reuses_code_and_different_urls_do_not(self):
        for table_class in self.table_classes:
            with self.subTest(table=table_class.__name__):
                shortener = Shortener(table_class=table_class, capacity=7)
                first = shortener.shorten("http://example.com/one")
                self.assertEqual(
                    shortener.shorten("http://example.com/one"), first
                )
                self.assertNotEqual(
                    shortener.shorten("http://example.com/two"), first
                )

    def test_rejects_invalid_urls(self):
        for table_class in self.table_classes:
            shortener = Shortener(table_class=table_class, capacity=7)
            for url in (
                "",
                "example.com/path",
                "ftp://example.com/file",
                "https:///missing-host",
                "https://example.com/white space",
                "https://[invalid",
            ):
                with self.subTest(table=table_class.__name__, url=url):
                    with self.assertRaises(ValueError):
                        shortener.shorten(url)

    def test_rejects_non_string_url_and_unknown_code(self):
        for table_class in self.table_classes:
            shortener = Shortener(table_class=table_class, capacity=7)
            with self.subTest(table=table_class.__name__):
                with self.assertRaises(TypeError):
                    shortener.shorten(1)
                with self.assertRaises(KeyError):
                    shortener.expand("unknown")


if __name__ == "__main__":
    unittest.main()
