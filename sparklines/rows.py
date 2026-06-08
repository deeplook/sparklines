"""Row allocation for multi-line and mixed positive/negative sparklines."""

import math
from typing import Literal, Optional, Union

NumLines = Union[int, Literal["auto"], tuple[int, int]]


def proportional(pos_max: float, neg_max: float, i: int, j: int) -> bool:
    """Return True if row split i:j is exactly proportional to the pos/neg range."""
    return math.isclose(pos_max * j, neg_max * i, rel_tol=0, abs_tol=1e-9)


def allocate_rows(pos_max: float, neg_max: float, n: int) -> tuple[int, int]:
    """Return best (up, down) row split approximating proportionality for n rows."""
    if n == 2:
        return 1, 1
    size = pos_max + neg_max
    ideal_i = n * pos_max / size
    target_i = round(ideal_i)
    best_i, best_j = 1, n - 1
    best_key: Optional[tuple[float, int, float, float]] = None
    for i in range(1, n):
        j = n - i
        imbalance = abs(pos_max * j - neg_max * i)
        key = (imbalance, abs(i - j), abs(i - ideal_i), abs(i - target_i))
        if best_key is None or key < best_key:
            best_key = key
            best_i, best_j = i, j
    return best_i, best_j


def ideal_num_rows(pos_max: float, neg_max: float) -> int:
    """Return the smallest total row count that yields an exactly proportional split.

    Falls back to the closest approximation within 10 rows if no exact split exists.
    """
    best_n = 2
    best_imbalance = float("inf")
    for n in range(2, 101):
        i, j = allocate_rows(pos_max, neg_max, n)
        if proportional(pos_max, neg_max, i, j):
            return n
        imbalance = abs(pos_max * j - neg_max * i)
        if imbalance < best_imbalance and n <= 10:
            best_imbalance = imbalance
            best_n = n
    return best_n


def resolve_mixed_rows(
    num_lines: NumLines, pos_max: float, neg_max: float
) -> tuple[int, int]:
    """Resolve a NumLines spec into a concrete (up_rows, down_rows) pair."""
    if isinstance(num_lines, tuple):
        return num_lines
    n = ideal_num_rows(pos_max, neg_max) if num_lines == "auto" else max(num_lines, 2)
    return allocate_rows(pos_max, neg_max, n)


def _resolve_nl(num_lines: NumLines, side: Literal["pos", "neg"]) -> int:
    """Resolve NumLines to a concrete row count for one side of a non-split render."""
    if num_lines == "auto":
        return 1
    if isinstance(num_lines, tuple):
        return num_lines[0] if side == "pos" else num_lines[1]
    return num_lines
