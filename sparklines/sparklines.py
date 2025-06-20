#!/usr/bin/env python

"""
Text-based sparklines, e.g. on the command-line like this: ▃▁▄▁▄█▂▅.

Please read the file README.rst for more information.
"""

import re
import sys
import warnings
from typing import Any, Optional, Sequence, Union

try:
    import termcolor

    HAVE_TERMCOLOR = True
except ImportError:
    HAVE_TERMCOLOR = False


blocks = " ▁▂▃▄▅▆▇█"


def _check_negatives(numbers: list[Optional[float]]) -> None:
    """Raise warning for negative numbers."""

    negatives = filter(lambda x: x < 0, filter(None, numbers))
    if any(negatives):
        neg_values = ", ".join(map(str, negatives))
        msg = "Found negative value(s): {0!s}. ".format(neg_values)
        msg += "While not forbidden, the output will look unexpected."
        warnings.warn(msg)


def _check_emphasis(numbers: list[Optional[float]], emph: list[str]) -> dict[int, str]:
    """Find index postions in list of numbers to be emphasized according to emph."""

    pat = r"(\w+)\:(eq|gt|ge|lt|le)\:(.+)"
    # find values to be highlighted
    emphasized = {}  # index: color
    for i, n in enumerate(numbers):
        if n is None:
            continue
        for em in emph:
            match = re.match(pat, em)
            if match is None:
                continue
            color, op, value = match.groups()
            value = float(value)
            if op == "eq" and n == value:
                emphasized[i] = color
            elif op == "gt" and n > value:
                emphasized[i] = color
            elif op == "ge" and n >= value:
                emphasized[i] = color
            elif op == "lt" and n < value:
                emphasized[i] = color
            elif op == "le" and n <= value:
                emphasized[i] = color
    return emphasized


def scale_values(
    numbers: list[Optional[float]],
    num_lines: int = 1,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> list[Optional[int]]:
    """Scale input numbers to appropriate range."""

    # find min/max values, ignoring Nones
    filtered = [n for n in numbers if n is not None]
    min_ = min(filtered) if minimum is None else minimum
    max_ = max(filtered) if maximum is None else maximum
    dv = max_ - min_

    # clamp
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


def sparklines(
    numbers: Optional[list[Optional[float]]] = None,
    num_lines: int = 1,
    emph: Optional[list[str]] = None,
    verbose: bool = False,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    wrap: Optional[int] = None,
) -> list[str]:
    """
    Return a list of 'sparkline' strings for a given list of input numbers.

    The list of input numbers may contain None values, too, for which the
    resulting sparkline will contain a blank character (a space).

    Examples:

        sparklines([3, 1, 4, 1, 5, 9, 2, 6])
        -> ['▃▁▄▁▄█▂▅']
        sparklines([3, 1, 4, 1, 5, 9, 2, 6], num_lines=2)
        -> [
            '     █ ▂',
            '▅▁▆▁██▃█'
        ]
    """
    if numbers is None:
        numbers = []

    assert num_lines > 0

    if len(numbers) == 0:
        return [""]

    # raise warning for negative numbers
    _check_negatives(numbers)

    values = scale_values(
        numbers, num_lines=num_lines, minimum=minimum, maximum=maximum
    )

    # find values to be highlighted
    emphasized = _check_emphasis(numbers, emph) if emph else {}

    point_index = 0
    subgraphs = []
    for subgraph_values in batch(wrap, values):
        multi_values = []
        for i in range(num_lines):
            multi_values.append(
                [min(v, 8) if v is not None else None for v in subgraph_values]
            )
            subgraph_values = [
                max(0, v - 8) if v is not None else None for v in subgraph_values
            ]
        multi_values.reverse()
        lines = []
        for subgraph_values in multi_values:
            if HAVE_TERMCOLOR and emphasized:
                tc = termcolor.colored
                res = [
                    (
                        tc(blocks[int(v)], emphasized.get(point_index + i, "white"))
                        if v is not None
                        else " "
                    )
                    for (i, v) in enumerate(subgraph_values)
                ]
            else:
                res = [
                    blocks[int(v)] if v is not None else " " for v in subgraph_values
                ]
            lines.append("".join(res))
        subgraphs.append(lines)
        point_index += len(subgraph_values)

    return list_join("", subgraphs)


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
    result = []
    for lst, _next in zip(lists[:], lists[1:]):
        result.extend(lst)
        result.append(separator)

    if lists:
        result.extend(lists[-1])
    return result


def demo(nums: Optional[list[Optional[float]]] = None) -> str:
    """Print a few usage examples on stdout."""
    if nums is None:
        nums = []

    nums = nums or [3, 1, 4, 1, 5, 9, 2, 6]

    def fmt(num: Union[float, int, None]) -> str:
        return "{0:g}".format(num) if isinstance(num, (float, int)) else "None"

    nums1 = list(map(fmt, nums))

    if __name__ == "__main__":
        prog = sys.argv[0]
    else:
        prog = "sparklines"

    result = []

    result.append("Usage examples (command-line and programmatic use):")
    result.append("")

    result.append("- Standard one-line sparkline")
    result.append("{0!s} {1!s}".format(prog, " ".join(nums1)))
    result.append(">>> print(sparklines([{0!s}])[0])".format(", ".join(nums1)))
    result.append(sparklines(nums)[0])
    result.append("")

    result.append("- Multi-line sparkline (n=2)")
    result.append("{0!s} -n 2 {1!s}".format(prog, " ".join(nums1)))
    result.append(
        ">>> for line in sparklines([{0!s}], num_lines=2): print(line)".format(
            ", ".join(nums1)
        )
    )
    for line in sparklines(nums, num_lines=2):
        result.append(line)
    result.append("")

    result.append("- Multi-line sparkline (n=3)")
    result.append("{0!s} -n 3 {1!s}".format(prog, " ".join(nums1)))
    result.append(
        ">>> for line in sparklines([{0!s}], num_lines=3): print(line)".format(
            ", ".join(nums1)
        )
    )
    for line in sparklines(nums, num_lines=3):
        result.append(line)
    result.append("")

    nums = nums + [None] + list(reversed(nums[:]))
    result.append("- Standard one-line sparkline with gap")
    result.append("{0!s} {1!s}".format(prog, " ".join(map(str, nums))))
    result.append(">>> print(sparklines([{0!s}])[0])".format(", ".join(map(str, nums))))
    result.append(sparklines(nums)[0])
    return "\n".join(result) + "\n"
