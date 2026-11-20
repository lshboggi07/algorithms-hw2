import unittest

from src.hash_table import HashTable, LinearProbingHashTable, horner_hash


class HornerHashTests(unittest.TestCase):
    def test_hash_uses_horner_polynomial_modulo_capacity(self):
        self.assertEqual(horner_hash("abc", 11), 5)

    def test_hash_rejects_invalid_key_and_capacity(self):
        with self.assertRaises(TypeError):
            horner_hash(1, 11)
        with self.assertRaises(ValueError):
            horner_hash("key", 0)


class HashTableTests(unittest.TestCase):
    def test_none_max_load_keeps_the_configured_capacity(self):
        table = HashTable(capacity=2, max_load=None)
        for value, key in enumerate(("a", "c", "e", "g", "i")):
            table.put(key, value)

        self.assertEqual(table.capacity, 2)
        self.assertEqual(len(table), 5)

    def test_fixed_capacity_table_rejects_a_load_limit(self):
        with self.assertRaises(ValueError):
            HashTable(capacity=2, max_load=0.75)

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

    def test_long_collision_chain_counts_each_node(self):
        table = HashTable(capacity=2)
        colliding_keys = ("a", "c", "e", "g")
        for value, key in enumerate(colliding_keys):
            table.put(key, value)

        for expected_probes, key in enumerate(colliding_keys, start=1):
            with self.subTest(key=key):
                result = table.probe(key)
                self.assertTrue(result.found)
                self.assertEqual(result.value, expected_probes - 1)
                self.assertEqual(result.probes, expected_probes)

        missing = table.probe("i")
        self.assertFalse(missing.found)
        self.assertEqual(missing.probes, len(colliding_keys))

    def test_probe_reports_hash_calculation(self):
        result = HashTable(capacity=11).probe("abc")
        self.assertEqual(result.hash_index, 5)
        self.assertEqual(
            result.hash_steps,
            (("a", 97, 9), ("b", 98, 3), ("c", 99, 5)),
        )


class LinearProbingHashTableTests(unittest.TestCase):
    def test_collisions_wrap_from_last_slot_to_first(self):
        table = LinearProbingHashTable(capacity=5)
        table.put("c", 1)
        table.put("h", 2)
        table.put("m", 3)

        self.assertEqual(table.snapshot()[4], (("c", 1),))
        self.assertEqual(table.snapshot()[0], (("h", 2),))
        self.assertEqual(table.snapshot()[1], (("m", 3),))
        result = table.probe("m")
        self.assertEqual(result.probe_path, (4, 0, 1))
        self.assertEqual(result.probes, 3)

    def test_missing_key_and_full_table_are_bounded(self):
        table = LinearProbingHashTable(capacity=2)
        table.put("a", 1)
        table.put("b", 2)
        missing = table.probe("c")
        self.assertFalse(missing.found)
        self.assertEqual(missing.probes, 2)
        with self.assertRaises(OverflowError):
            table.put("c", 3)

        table.put("a", 4)
        self.assertEqual(table.get("a"), 4)
        self.assertEqual(len(table), 2)


if __name__ == "__main__":
    unittest.main()
