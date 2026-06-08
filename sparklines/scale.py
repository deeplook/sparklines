"""Value scaling and sequence utilities: scale_values, batch, list_join."""

from collections.abc import Sequence
from typing import Any, Optional

from sparklines.ansi import blocks


def scale_values(
    numbers: Sequence[Optional[float]],
    num_lines: int = 1,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> list[Optional[int]]:
    """Scale input numbers to appropriate range."""
    filtered = [n for n in numbers if n is not None]
    min_ = min(filtered) if minimum is None else minimum
    max_ = max(filtered) if maximum is None else maximum
    dv = max_ - min_

    numbers = [max(min(n, max_), min_) if n is not None else None for n in numbers]

    if dv == 0:
        values = [4 * num_lines if x is not None else None for x in numbers]
    elif dv > 0:
        num_blocks = len(blocks) - 1
        min_index = 1.0
        max_index = num_lines * num_blocks
        values_f = [
            (
                ((max_index - min_index) * (x - min_)) / dv + min_index
                if x is not None
                else None
            )
            for x in numbers
        ]
        values = [round(v) or 1 if v is not None else None for v in values_f]
    return values


def batch(batch_size: Optional[int], items: Sequence[Any]) -> list[list[Any]]:
    """Batch items into groups of batch_size."""
    items = list(items)
    if batch_size is None:
        return [items]
    MISSING = object()
    padded_items = items + [MISSING] * (batch_size - 1)
    groups = zip(*[padded_items[i::batch_size] for i in range(batch_size)])
    return [[item for item in group if item != MISSING] for group in groups]


def list_join(separator: str, lists: list[list[Any]]) -> list[Any]:
    """Join a list of lists with separator items between each sublist."""
    result = []
    for lst, _next in zip(lists[:], lists[1:]):
        result.extend(lst)
        result.append(separator)
    if lists:
        result.extend(lists[-1])
    return result
