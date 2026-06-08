"""Colour emphasis evaluation: value-based and index-slice expressions."""

import re
from collections.abc import Sequence
from typing import Optional


def _check_emphasis(
    numbers: Sequence[Optional[float]], emph: list[str]
) -> dict[int, str]:
    """Find index positions in list of numbers to be emphasized according to emph."""
    val_pat = r"(\w+)\:(eq|gt|ge|lt|le)\:(.+)"
    idx_pat = r"(\w+)\:\[([^\]]*)\]"
    emphasized: dict[int, str] = {}

    def _int_or_none(s: Optional[str]) -> Optional[int]:
        return int(s) if s else None

    for em in emph:
        idx_match = re.fullmatch(idx_pat, em)
        if idx_match:
            color, slice_str = idx_match.groups()
            parts = (slice_str.split(":") + [None, None, None])[:3]
            sl = slice(
                _int_or_none(parts[0]), _int_or_none(parts[1]), _int_or_none(parts[2])
            )
            for i in range(*sl.indices(len(numbers))):
                if numbers[i] is not None:
                    emphasized[i] = color
            continue
        for i, n in enumerate(numbers):
            if n is None:
                continue
            match = re.fullmatch(val_pat, em)
            if match is None:
                continue
            color, op, value_str = match.groups()
            v = float(value_str)
            ops = {
                "eq": n == v,
                "gt": n > v,
                "ge": n >= v,
                "lt": n < v,
                "le": n <= v,
            }
            if ops.get(op):
                emphasized[i] = color
    return emphasized
