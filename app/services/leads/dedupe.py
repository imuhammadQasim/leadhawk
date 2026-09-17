import re

_BUSINESS_SUFFIXES = re.compile(r"\b(llc|inc|ltd|co|corp|company)\b")
_NON_WORD = re.compile(r"[^\w\s]")
_WHITESPACE = re.compile(r"\s+")


def normalize_business_name(name: str) -> str:
    """Collapse punctuation/casing/legal-suffix differences so 'Joe's Pizza'
    and 'Joes Pizza LLC' compare equal."""
    normalized = name.lower()
    normalized = _NON_WORD.sub("", normalized)
    normalized = _BUSINESS_SUFFIXES.sub("", normalized)
    return _WHITESPACE.sub(" ", normalized).strip()


def normalize_address(address: str | None) -> str | None:
    if not address:
        return None
    normalized = address.lower()
    normalized = _NON_WORD.sub("", normalized)
    return _WHITESPACE.sub(" ", normalized).strip()
