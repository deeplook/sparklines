#!/usr/bin/env python

"""
Text-based sparklines, e.g. on the command-line like this: ▃▁▄▁▄█▂▅.

Please read the file README.rst for more information.
"""

import math
import os
import re
import sys
from typing import Any, Literal, Optional, Sequence, Union

try:
    import termcolor

    HAVE_TERMCOLOR = True
except ImportError:
    HAVE_TERMCOLOR = False


NumLines = Union[int, Literal["auto"], tuple[int, int]]

blocks = " ▁▂▃▄▅▆▇█"
# Complement index: blocks[8 - i] gives the upward char whose reverse-video
# rendering produces a downward bar of height i/8.
_COMPLEMENT = [8 - i for i in range(9)]
# Unicode-only fallback for inverted bars when ANSI is suppressed (NO_COLOR etc.).
# Maps scaled height 0-8 to the closest available top-fill Unicode character.
_INVERTED_UNICODE = " ▔▔▔▀▀▀▀█"


def _ansi_ok() -> bool:
    """Return True if emitting ANSI escape codes is appropriate.

    Respects NO_COLOR, ANSI_COLORS_DISABLED, and TERM=dumb, but does NOT
    require a TTY — inverted=True is an explicit opt-in to ANSI output.
    """
    if os.environ.get("NO_COLOR") or os.environ.get("ANSI_COLORS_DISABLED"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return True


def _inverted_char(v: int, color: Optional[str] = None) -> str:
    """Return a character representing a downward bar of height v/8.

    When ANSI is available, uses the complement upward block character under
    reverse video, giving full 8-level resolution. Falls back to the closest
    top-fill Unicode character (▔/▀/█) when ANSI is suppressed by NO_COLOR,
    ANSI_COLORS_DISABLED, or TERM=dumb.
    """
    if v == 0:
        return " "
    if v == 8:
        if color and HAVE_TERMCOLOR and _ansi_ok():
            return termcolor.colored("█", color, force_color=True)
        return "█"
    if not _ansi_ok():
        return _INVERTED_UNICODE[v]
    ch = blocks[_COMPLEMENT[v]]
    if HAVE_TERMCOLOR:
        return termcolor.colored(ch, color, attrs=["reverse"], force_color=True)
    return f"\033[7m{ch}\033[27m"


def _check_emphasis(
    numbers: Sequence[Optional[float]], emph: list[str]
) -> dict[int, str]:
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
    numbers: Sequence[Optional[float]],
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
    if num_lines == "auto":
        n = ideal_num_rows(pos_max, neg_max)
    else:
        n = max(num_lines, 2)
    return allocate_rows(pos_max, neg_max, n)


def _resolve_nl(num_lines: NumLines, side: Literal["pos", "neg"]) -> int:
    """Resolve NumLines to a concrete row count for one side of a non-split render."""
    if num_lines == "auto":
        return 1
    if isinstance(num_lines, tuple):
        return num_lines[0] if side == "pos" else num_lines[1]
    return num_lines


def _render_row(
    row_values: list[Optional[int]],
    point_base: int,
    inverted: bool,
    emphasized: dict[int, str],
) -> str:
    """Render one horizontal row of scaled bar values to a string."""
    if inverted:
        return "".join(
            (
                _inverted_char(
                    v,
                    emphasized.get(point_base + i)
                    if HAVE_TERMCOLOR and emphasized
                    else None,
                )
                if v is not None
                else " "
            )
            for i, v in enumerate(row_values)
        )
    if HAVE_TERMCOLOR and emphasized:
        return "".join(
            (
                termcolor.colored(
                    blocks[int(v)], emphasized.get(point_base + i, "white")
                )
                if v is not None
                else " "
            )
            for i, v in enumerate(row_values)
        )
    return "".join(blocks[int(v)] if v is not None else " " for v in row_values)


def _render_series(
    numbers: Sequence[Optional[float]],
    num_lines: int = 1,
    emph: Optional[list[str]] = None,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    wrap: Optional[int] = None,
    inverted: bool = False,
) -> list[str]:
    """Render a sequence of scaled numbers as a list of sparkline strings."""
    if inverted:
        numbers = [abs(v) if v is not None and v < 0 else v for v in numbers]

    values = scale_values(
        numbers, num_lines=num_lines, minimum=minimum, maximum=maximum
    )

    emphasized = _check_emphasis(numbers, emph) if emph else {}

    point_index = 0
    subgraphs = []
    for batch_values in batch(wrap, values):
        remaining: list[Optional[int]] = list(batch_values)
        multi_values = []
        for _ in range(num_lines):
            multi_values.append(
                [min(v, 8) if v is not None else None for v in remaining]
            )
            remaining = [max(0, v - 8) if v is not None else None for v in remaining]
        if not inverted:
            multi_values.reverse()
        lines = [
            _render_row(row_values, point_index, inverted, emphasized)
            for row_values in multi_values
        ]
        subgraphs.append(lines)
        point_index += len(batch_values)

    return list_join("", subgraphs)


def _partition_series(
    numbers: Sequence[Optional[float]],
    zero: Literal["up", "none"],
) -> tuple[list[Optional[float]], list[Optional[float]], float, float]:
    """Split numbers into (pos_series, neg_series, pos_max, neg_max)."""
    if zero == "up":
        pos: list[Optional[float]] = [
            v if v is not None and v >= 0 else None for v in numbers
        ]
    else:
        pos = [v if v is not None and v > 0 else None for v in numbers]
    neg: list[Optional[float]] = [
        abs(v) if v is not None and v < 0 else None for v in numbers
    ]
    pos_max = max((v for v in pos if v is not None), default=0.0)
    neg_max = max((v for v in neg if v is not None), default=0.0)
    return pos, neg, pos_max, neg_max


def _render_split(
    numbers: Sequence[Optional[float]],
    num_lines: NumLines,
    emph: Optional[list[str]],
    wrap: Optional[int],
    zero: Literal["up", "none"],
) -> list[str]:
    """Render mixed positive/negative data as stacked up/down sparkline rows."""
    pos, neg, pos_max, neg_max = _partition_series(numbers, zero)
    up_rows, down_rows = resolve_mixed_rows(num_lines, pos_max, neg_max)

    if isinstance(num_lines, tuple):
        pos_M, neg_M = pos_max, neg_max
    else:
        shared = max(pos_max, neg_max)
        pos_M = neg_M = shared

    pos_lines = _render_series(
        pos,
        up_rows,
        emph=emph,
        minimum=0.0,
        maximum=pos_M,
        wrap=wrap,
    )
    neg_lines = _render_series(
        neg,
        down_rows,
        emph=emph,
        minimum=0.0,
        maximum=neg_M,
        wrap=wrap,
        inverted=True,
    )
    return pos_lines + neg_lines


def _validate_num_lines(num_lines: NumLines) -> None:
    """Raise ValueError if num_lines is not a valid row-count spec."""
    if isinstance(num_lines, int) and num_lines > 0:
        return
    if num_lines == "auto":
        return
    if isinstance(num_lines, tuple) and all(n > 0 for n in num_lines):
        return
    raise ValueError(
        f"num_lines must be a positive int, 'auto', or (up, down) tuple; "
        f"got {num_lines!r}"
    )


def sparklines(
    numbers: Optional[Sequence[Optional[float]]] = None,
    num_lines: NumLines = 1,
    emph: Optional[list[str]] = None,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    wrap: Optional[int] = None,
    zero: Literal["up", "none"] = "up",
) -> list[str]:
    """
    Return a list of 'sparkline' strings for a given list of input numbers.

    The list of input numbers may contain None values, too, for which the
    resulting sparkline will contain a blank character (a space).

    Mixed positive/negative data is automatically split into two rows: upward
    bars for positives on top, downward bars for negatives below.

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
    _validate_num_lines(num_lines)

    if len(numbers) == 0:
        return [""]

    filtered = [n for n in numbers if n is not None]
    if not filtered:
        return [""]

    mn, mx = min(filtered), max(filtered)

    if mn < 0 < mx:
        return _render_split(numbers, num_lines, emph, wrap, zero)

    if mn < 0:
        neg_only: list[Optional[float]] = [
            abs(v) if v is not None else None for v in numbers
        ]
        return _render_series(
            neg_only,
            _resolve_nl(num_lines, "neg"),
            emph,
            minimum=minimum,
            maximum=maximum,
            wrap=wrap,
            inverted=True,
        )

    return _render_series(
        numbers,
        _resolve_nl(num_lines, "pos"),
        emph,
        minimum,
        maximum,
        wrap,
    )


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
    result.append(
        ">>> for line in sparklines([{0!s}]): print(line)".format(", ".join(nums1))
    )
    for line in sparklines(nums):
        result.append(line)
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

    nums_gap = nums + [None] + list(reversed(nums[:]))
    result.append("- Standard one-line sparkline with gap")
    result.append("{0!s} {1!s}".format(prog, " ".join(map(str, nums_gap))))
    result.append(
        ">>> for line in sparklines([{0!s}]): print(line)".format(
            ", ".join(map(str, nums_gap))
        )
    )
    for line in sparklines(nums_gap):
        result.append(line)
    result.append("")

    mixed_nums = [3, -1, 4, -1, 5, -9, 2, -6]
    mixed_nums1 = list(map(fmt, mixed_nums))
    result.append("- Auto-split sparkline (mixed positive and negative values)")
    result.append("{0!s} {1!s}".format(prog, " ".join(mixed_nums1)))
    result.append(
        ">>> for line in sparklines([{0!s}]): print(line)".format(
            ", ".join(mixed_nums1)
        )
    )
    for line in sparklines(mixed_nums):
        result.append(line)
    result.append("")

    auto_nums = [1, 2, 3, -1, -2, -3, 0, 4, 5, 6]
    auto_nums1 = list(map(fmt, auto_nums))
    result.append("- Auto-split with proportional rows (-n auto)")
    result.append("{0!s} -n auto {1!s}".format(prog, " ".join(auto_nums1)))
    result.append(
        ">>> for line in sparklines([{0!s}], num_lines='auto'): print(line)".format(
            ", ".join(auto_nums1)
        )
    )
    for line in sparklines(auto_nums, num_lines="auto"):
        result.append(line)
    result.append("")

    result.append("- Explicit row layout (-n 2:1)")
    result.append("{0!s} -n 2:1 {1!s}".format(prog, " ".join(auto_nums1)))
    result.append(
        ">>> for line in sparklines([{0!s}], num_lines=(2,1)): print(line)".format(
            ", ".join(auto_nums1)
        )
    )
    for line in sparklines(auto_nums, num_lines=(2, 1)):
        result.append(line)
    result.append("")

    zero_nums = [0, 1, 2, -1, -2, 0]
    zero_nums1 = list(map(fmt, zero_nums))
    result.append("- Zero on positive baseline (--zero up, default)")
    result.append("{0!s} --zero up {1!s}".format(prog, " ".join(zero_nums1)))
    result.append(
        ">>> for line in sparklines([{0!s}], zero='up'): print(line)".format(
            ", ".join(zero_nums1)
        )
    )
    for line in sparklines(zero_nums, zero="up"):
        result.append(line)
    result.append("")

    result.append("- Zeros omitted from both sides (--zero none)")
    result.append("{0!s} --zero none {1!s}".format(prog, " ".join(zero_nums1)))
    result.append(
        ">>> for line in sparklines([{0!s}], zero='none'): print(line)".format(
            ", ".join(zero_nums1)
        )
    )
    for line in sparklines(zero_nums, zero="none"):
        result.append(line)
    return "\n".join(result) + "\n"
