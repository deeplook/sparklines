"""Rendering pipeline: single rows, series, partition, and mixed split."""

from collections.abc import Sequence
from typing import Literal, Optional

from sparklines.ansi import HAVE_TERMCOLOR, _inverted_char, blocks
from sparklines.emphasis import _check_emphasis
from sparklines.rows import NumLines, resolve_mixed_rows
from sparklines.scale import batch, list_join, scale_values

import contextlib

with contextlib.suppress(ImportError):
    import termcolor


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
    emphasized: Optional[dict[int, str]] = None,
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

    if emphasized is None:
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

    emphasized = _check_emphasis(numbers, emph) if emph else {}

    pos_scaled = scale_values(pos, num_lines=up_rows, minimum=0.0, maximum=pos_M)
    neg_scaled = scale_values(neg, num_lines=down_rows, minimum=0.0, maximum=neg_M)

    def _multi(scaled: list[Optional[int]], n: int) -> list[list[Optional[int]]]:
        remaining = list(scaled)
        rows = []
        for _ in range(n):
            rows.append([min(v, 8) if v is not None else None for v in remaining])
            remaining = [max(0, v - 8) if v is not None else None for v in remaining]
        return rows

    subgraphs = []
    point_index = 0
    for pos_win, neg_win in zip(batch(wrap, pos_scaled), batch(wrap, neg_scaled)):
        pos_rows = list(reversed(_multi(pos_win, up_rows)))
        neg_rows = _multi(neg_win, down_rows)
        lines = [
            _render_row(row, point_index, False, emphasized) for row in pos_rows
        ] + [_render_row(row, point_index, True, emphasized) for row in neg_rows]
        subgraphs.append(lines)
        point_index += len(pos_win)

    return list_join("", subgraphs)
