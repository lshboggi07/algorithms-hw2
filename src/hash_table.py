"""A string-keyed separate-chaining hash table with explicit probe tracking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


HashStep = tuple[str, int, int]


def _hash_details(key: str, capacity: int) -> tuple[int, tuple[HashStep, ...]]:
    if not isinstance(key, str):
        raise TypeError("key must be a string")
    if type(capacity) is not int or capacity <= 0:
        raise ValueError("capacity must be a positive integer")

    value = 0
    steps: list[HashStep] = []
    for character in key:
        codepoint = ord(character)
        value = (31 * value + codepoint) % capacity
        steps.append((character, codepoint, value))
    return value, tuple(steps)


def horner_hash(key: str, capacity: int) -> int:
    """Return a string's polynomial hash modulo the table capacity."""
    return _hash_details(key, capacity)[0]


@dataclass(frozen=True)
class ProbeResult:
    value: Any
    found: bool
    probes: int
    hash_index: int
    hash_steps: tuple[HashStep, ...]


@dataclass
class _Node:
    key: str
    value: Any
    next: _Node | None = None


class HashTable:
    """Fixed-capacity separate chaining table for string keys."""

    def __init__(self, capacity: int = 101) -> None:
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._buckets: list[_Node | None] = [None] * capacity
        self._size = 0

    def put(self, key: str, value: Any) -> None:
        index, _ = _hash_details(key, self.capacity)
        node = self._buckets[index]
        if node is None:
            self._buckets[index] = _Node(key, value)
            self._size += 1
            return

        while True:
            if node.key == key:
                node.value = value
                return
            if node.next is None:
                node.next = _Node(key, value)
                self._size += 1
                return
            node = node.next

    def probe(self, key: str) -> ProbeResult:
        index, steps = _hash_details(key, self.capacity)
        node = self._buckets[index]
        probes = 0
        while node is not None:
            probes += 1
            if node.key == key:
                return ProbeResult(node.value, True, probes, index, steps)
            node = node.next
        return ProbeResult(None, False, probes, index, steps)

    def get(self, key: str, default: Any = None) -> Any:
        result = self.probe(key)
        return result.value if result.found else default

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return self.probe(key).found

    def __len__(self) -> int:
        return self._size

    def snapshot(self) -> tuple[tuple[tuple[str, Any], ...], ...]:
        """Return buckets in slot order, preserving each chain's order."""
        buckets: list[tuple[tuple[str, Any], ...]] = []
        for head in self._buckets:
            entries: list[tuple[str, Any]] = []
            node = head
            while node is not None:
                entries.append((node.key, node.value))
                node = node.next
            buckets.append(tuple(entries))
        return tuple(buckets)
