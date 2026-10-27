"""Generic helpers for functional programming."""

from __future__ import annotations

from collections.abc import Callable
from functools import reduce
from typing import Any


def identity(value: Any) -> Any:
    """Return the value unchanged."""
    return value


def compose(*functions: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """Combine functions into one, applied left to right: compose(f, g)(x) == g(f(x))."""
    return reduce(lambda f, g: lambda x: g(f(x)), functions, identity)
