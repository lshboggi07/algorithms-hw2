"""Base62 encoding and decoding utilities."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode(number: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if type(number) is not int:
        raise TypeError("number must be an integer")
    if number < 0:
        raise ValueError("number must be non-negative")
    if number == 0:
        return ALPHABET[0]

    encoded = ""
    while number:
        number, remainder = divmod(number, len(ALPHABET))
        encoded = ALPHABET[remainder] + encoded
    return encoded


def decode(code: str) -> int:
    """Decode a non-empty base62 string to a non-negative integer."""
    if not isinstance(code, str):
        raise TypeError("code must be a string")
    if not code:
        raise ValueError("code must not be empty")

    number = 0
    for character in code:
        digit = ALPHABET.find(character)
        if digit < 0:
            raise ValueError(f"invalid base62 character: {character!r}")
        number = number * len(ALPHABET) + digit
    return number
