"""In-memory URL shortening backed by a selectable hash-table implementation."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable


class Shortener:
    def __init__(
        self, table_class: type[HashTable] = HashTable, capacity: int = 101
    ) -> None:
        self._url_to_code = table_class(capacity=capacity)
        self._code_to_url = table_class(capacity=capacity)
        self._next_id = 1

    @property
    def table(self) -> HashTable:
        """The URL index used by this shortener."""
        return self._url_to_code

    @staticmethod
    def _validate_url(url: str) -> None:
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        if not url or any(character.isspace() for character in url):
            raise ValueError("url must be non-empty and contain no whitespace")

        try:
            parts = urlsplit(url)
            hostname = parts.hostname
            parts.port
        except ValueError as error:
            raise ValueError(f"invalid URL: {url!r}") from error

        if parts.scheme.lower() not in ("http", "https") or not hostname:
            raise ValueError("url must be an absolute HTTP or HTTPS URL")

    def shorten(self, url: str) -> str:
        self._validate_url(url)
        existing = self._url_to_code.probe(url)
        if existing.found:
            return existing.value

        code = encode(self._next_id)
        self._next_id += 1
        self._url_to_code.put(url, code)
        self._code_to_url.put(code, url)
        return code

    def expand(self, code: str) -> str:
        if not isinstance(code, str):
            raise TypeError("code must be a string")
        result = self._code_to_url.probe(code)
        if not result.found:
            raise KeyError(code)
        return result.value
