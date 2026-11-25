"""Shared verdict helpers: a result and plain JSON forms of contract instances."""

import dataclasses
from enum import Enum

# What a check could raise on a value it never expected: the entry points turn it into a failed verdict
# that names it, because a verifier that raises leaves the run with no verdict at all.
UNEXPECTED = (ArithmeticError, AttributeError, LookupError, OSError, RecursionError, StopIteration, TypeError,
              ValueError)


def result(valid, message, *, score=None, **details):
    return {"valid": valid, "score": float(valid) if score is None else float(score), "message": message,
            "details": details}


def plain(value):
    """A contract instance (or anything inside one) as plain JSON values: Enum members as their values."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return plain(dataclasses.asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {plain(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def compared(name, given, wanted):
    """A verify_output verdict: the tool's output equals what the bundled data gives."""
    if given == wanted:
        return result(True, f"{name} output matches the bundled data")
    given_plain, wanted_plain = plain(given), plain(wanted)
    different = sorted(key for key in set(given_plain) | set(wanted_plain)
                       if given_plain.get(key) != wanted_plain.get(key))
    return result(False, f"{name} output differs from the bundled data at {', '.join(different)}")
