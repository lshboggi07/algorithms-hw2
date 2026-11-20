import unittest

from src.hash_table import HashTable, horner_hash


class HornerHashTests(unittest.TestCase):
    def test_hash_uses_horner_polynomial_modulo_capacity(self):
        self.assertEqual(horner_hash("abc", 11), 5)

    def test_hash_rejects_invalid_key_and_capacity(self):
        with self.assertRaises(TypeError):
            horner_hash(1, 11)
        with self.assertRaises(ValueError):
            horner_hash("key", 0)


class HashTableTests(unittest.TestCase):
    def test_missing_key_and_empty_key(self):
        table = HashTable(capacity=3)
        self.assertEqual(len(table), 0)
        self.assertNotIn("", table)
        self.assertIsNone(table.get("missing"))
        table.put("", "empty")
        self.assertIn("", table)
        self.assertEqual(table.get(""), "empty")

    def test_collisions_preserve_values_and_overwrite_in_place(self):
        table = HashTable(capacity=2)
        table.put("a", 1)
        table.put("c", 2)

        result = table.probe("c")
        self.assertTrue(result.found)
        self.assertEqual(result.value, 2)
        self.assertEqual(result.probes, 2)
        self.assertEqual(len(table), 2)

        table.put("a", 3)
        self.assertEqual(table.get("a"), 3)
        self.assertEqual(len(table), 2)

    def test_probe_reports_hash_calculation(self):
        result = HashTable(capacity=11).probe("abc")
        self.assertEqual(result.hash_index, 5)
        self.assertEqual(
            result.hash_steps,
            (("a", 97, 9), ("b", 98, 3), ("c", 99, 5)),
        )


if __name__ == "__main__":
    unittest.main()
