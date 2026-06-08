"""Text-based sparklines, e.g. on the command-line like this: ▃▁▄▁▄█▂▅.

Please read the file README.rst for more information.
"""

import sys
from collections.abc import Sequence
from typing import Any, Literal, Optional, Union

from sparklines.ansi import (  # noqa: F401
    HAVE_TERMCOLOR,
    _COMPLEMENT,
    _INVERTED_UNICODE,
    _ansi_ok,
    _inverted_char,
    blocks,
)
from sparklines.emphasis import _check_emphasis  # noqa: F401
from sparklines.render import (  # noqa: F401
    _partition_series,
    _render_row,
    _render_series,
    _render_split,
)
from sparklines.rows import (  # noqa: F401
    NumLines,
    _resolve_nl,
    allocate_rows,
    ideal_num_rows,
    proportional,
    resolve_mixed_rows,
)
from sparklines.scale import batch, list_join, scale_values  # noqa: F401


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
    """Return a list of 'sparkline' strings for a given list of input numbers.

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
        emph=emph,
        minimum=minimum,
        maximum=maximum,
        wrap=wrap,
    )


def _demo_lines(nums: list[Optional[float]]) -> list[str]:
    """Generate demo output lines without incremental list appending."""

    def fmt(num: Union[float, int, None]) -> str:
        return f"{num:g}" if isinstance(num, (float, int)) else "None"

    nums1 = list(map(fmt, nums))
    prog = sys.argv[0] if __name__ == "__main__" else "sparklines"
    nums_gap = nums + [None] + list(reversed(nums[:]))
    mixed_nums: list[Optional[float]] = [3, -1, 4, -1, 5, -9, 2, -6]
    mixed_nums1 = list(map(fmt, mixed_nums))
    auto_nums: list[Optional[float]] = [1, 2, 3, -1, -2, -3, 0, 4, 5, 6]
    auto_nums1 = list(map(fmt, auto_nums))
    zero_nums: list[Optional[float]] = [0, 1, 2, -1, -2, 0]
    zero_nums1 = list(map(fmt, zero_nums))

    return [
        "Usage examples (command-line and programmatic use):",
        "",
        "- Standard one-line sparkline",
        f"{prog} {' '.join(nums1)}",
        f">>> for line in sparklines([{', '.join(nums1)}]): print(line)",
        *sparklines(nums),
        "",
        "- Multi-line sparkline (n=2)",
        f"{prog} -n 2 {' '.join(nums1)}",
        f">>> for line in sparklines([{', '.join(nums1)}], num_lines=2): print(line)",
        *sparklines(nums, num_lines=2),
        "",
        "- Multi-line sparkline (n=3)",
        f"{prog} -n 3 {' '.join(nums1)}",
        f">>> for line in sparklines([{', '.join(nums1)}], num_lines=3): print(line)",
        *sparklines(nums, num_lines=3),
        "",
        "- Standard one-line sparkline with gap",
        f"{prog} {' '.join(map(str, nums_gap))}",
        f">>> for line in sparklines([{', '.join(map(str, nums_gap))}]): print(line)",
        *sparklines(nums_gap),
        "",
        "- Auto-split sparkline (mixed positive and negative values)",
        f"{prog} {' '.join(mixed_nums1)}",
        f">>> for line in sparklines([{', '.join(mixed_nums1)}]): print(line)",
        *sparklines(mixed_nums),
        "",
        "- Auto-split with proportional rows (-n auto)",
        f"{prog} -n auto {' '.join(auto_nums1)}",
        (
            f">>> for line in sparklines([{', '.join(auto_nums1)}],"
            f" num_lines='auto'): print(line)"
        ),
        *sparklines(auto_nums, num_lines="auto"),
        "",
        "- Explicit row layout (-n 2:1)",
        f"{prog} -n 2:1 {' '.join(auto_nums1)}",
        (
            f">>> for line in sparklines([{', '.join(auto_nums1)}],"
            f" num_lines=(2,1)): print(line)"
        ),
        *sparklines(auto_nums, num_lines=(2, 1)),
        "",
        "- Zero on positive baseline (--zero up, default)",
        f"{prog} --zero up {' '.join(zero_nums1)}",
        f">>> for line in sparklines([{', '.join(zero_nums1)}], zero='up'): print(line)",  # noqa: E501
        *sparklines(zero_nums, zero="up"),
        "",
        "- Zeros omitted from both sides (--zero none)",
        f"{prog} --zero none {' '.join(zero_nums1)}",
        (
            f">>> for line in sparklines([{', '.join(zero_nums1)}],"
            f" zero='none'): print(line)"
        ),
        *sparklines(zero_nums, zero="none"),
    ]


def demo(nums: Optional[list[Optional[float]]] = None) -> str:
    """Print a few usage examples on stdout."""
    if nums is None:
        nums = []
    nums = nums or [3, 1, 4, 1, 5, 9, 2, 6]
    return "\n".join(_demo_lines(nums)) + "\n"


# Suppress unused-import warnings for re-exported names consumed via star import.
__all__ = [
    "Any",
    "HAVE_TERMCOLOR",
    "NumLines",
    "Union",
    "_check_emphasis",
    "allocate_rows",
    "batch",
    "blocks",
    "demo",
    "ideal_num_rows",
    "list_join",
    "proportional",
    "resolve_mixed_rows",
    "scale_values",
    "sparklines",
]
