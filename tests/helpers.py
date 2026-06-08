"""Shared test helpers."""

import re


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from a string."""
    return re.compile(r"\x1b[^m]*m").sub("", text)
