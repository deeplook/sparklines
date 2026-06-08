#!/usr/bin/env python

"""
Run from the root folder with either 'python setup.py test' or
'py.test test/test_sparkline.py'.
"""

import os
import re
from pathlib import Path
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import pytest

from sparklines import batch, scale_values, sparklines, demo
from sparklines.sparklines import allocate_rows, ideal_num_rows
from sparklines.__main__ import test_valid_number as is_valid_number, main


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from a text."""
    # http://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python#14693789
    ansi_escape = re.compile(r"\x1b[^m]*m")
    return ansi_escape.sub("", text)


def test_parse_float() -> None:
    """Test parsing input numbers."""
    t = is_valid_number

    assert t("4.5") == "4.5"
    assert t("-4.5") == "-4.5"
    assert t("4.") == "4."
    assert t(".5") == ".5"
    assert t("4.5e0") == "4.5e0"
    assert t("-4.5e0") == "-4.5e0"
    assert t("-4.5e-2") == "-4.5e-2"
    assert t("-.5e-2") == "-.5e-2"

    assert t("4.5,") == "4.5"
    assert t("4.5;") == "4.5"
    assert t('"4.5"') == "4.5"
    assert t("(4.5)") == "4.5"

    assert t("null") == "null"
    assert t("Null") == "null"
    assert t("none") == "none"
    assert t("None") == "none"

    assert t("None,") == "none"

    with pytest.raises(ValueError):
        t(",")
    with pytest.raises(ValueError):
        t("invalid")


def test_scale0() -> None:
    """Test scale..."""
    res = scale_values([1, 2, 3])
    exp = [1.0, 4.0, 8.0]
    assert res == exp


def test_scale1() -> None:
    """Test scale..."""
    res = scale_values([1, 2, 3], num_lines=2)
    exp = [1.0, 8.0, 16.0]
    assert res == exp


def test_batch() -> None:
    batches = batch(3, range(10))
    assert batches == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]], batches

    batches = batch(None, range(3))
    assert batches == [[0, 1, 2]]


def test_scale_pi() -> None:
    """Test scale Pi."""
    res = scale_values([3, 1, 4, 1, 5, 9, 2, 6])
    exp = [3, 1, 4, 1, 4, 8, 2, 5]
    assert res == exp


def test_pi() -> None:
    """Test first eight digits of Pi."""
    res = sparklines([3, 1, 4, 1, 5, 9, 2, 6])
    exp = ["▃▁▄▁▄█▂▅"]
    assert res == exp


def test_minmax() -> None:
    """Test two values, min and max."""
    res = sparklines([1, 8])
    exp = ["▁█"]  # 1, 8
    assert res == exp


def test_rounding0() -> None:
    """Test two values, min and max."""
    res = sparklines([1, 5, 8])
    exp = ["▁▅█"]  # 1, 5, 8
    assert res == exp


def test_maximum() -> None:
    res = sparklines([1, 2, 3, 10, 10], maximum=3)
    exp = ["▁▄███"]
    assert res == exp


def test_maximum_internal_consistency() -> None:
    res = sparklines([1, 2, 3, 10, 10, 1], maximum=3)
    exp = sparklines([1, 2, 3, 3, 3, 1], maximum=3)
    assert res == exp


def test_minimum() -> None:
    res = sparklines([0, 0, 11, 12, 13], minimum=10)
    exp = ["▁▁▃▆█"]
    assert res == exp


def test_minimum_internal_consistency() -> None:
    res = sparklines([0, 0, 11, 12, 13], minimum=10)
    exp = sparklines([10, 10, 11, 12, 13], minimum=10)
    assert res == exp


def test1() -> None:
    """Test single values all have the same four pixel high output character."""
    for i in range(10):
        res = sparklines([i])
        exp = ["▄"]
        assert res == exp


def test_empty() -> None:
    """Make sure degenerate cases don't fail."""
    res = sparklines([])
    exp = [""]
    # Produces an empty line from the command line
    #   we might prefer empty output
    assert res == exp


def test_multiline() -> None:
    res = sparklines([1, 5, 8], num_lines=3)
    exp = ["  █", " ▆█", "▁██"]
    assert res == exp


def test_wrap() -> None:
    res = sparklines([1, 2, 3, 1, 2, 3, 1, 2], wrap=3)
    exp = ["▁▄█", "", "▁▄█", "", "▁▄"]
    assert res == exp


def test_wrap_scale() -> None:
    res = sparklines([100, 50, 100, 20, 50, 20, 1, 1, 1], wrap=3)
    exp = ["█▄█", "", "▂▄▂", "", "▁▁▁"]
    assert res == exp


def test_wrap_consistency() -> None:
    res = sparklines([1, 2, 3, 1, 2, 3, 1, 2], wrap=3)
    exp = (
        sparklines([1, 2, 3], maximum=3, minimum=1)
        + [""]
        + sparklines([1, 2, 3], maximum=3, minimum=1)
        + [""]
        + sparklines([1, 2], maximum=3, minimum=1)
    )
    assert res == exp


def test_wrap_escaping_consistency() -> None:
    no_emph = sparklines([1, 2, 3, 1, 2, 3, 1, 2], wrap=3)
    stripped_emph = map(
        strip_ansi, sparklines([1, 2, 3, 1, 2, 3, 1, 2], wrap=3, emph=["green:le:1.0"])
    )
    assert no_emph == list(stripped_emph)


def _test_wrap_escaping() -> None:
    res = sparklines([1, 10, 1, 10, 1, 10], emph=["green:ge:2.0"], wrap=3)
    exp = [
        "\x1b[37m▁\x1b[0m\x1b[32m█\x1b[0m\x1b[37m▁\x1b[0m",
        "",
        "\x1b[32m█\x1b[0m\x1b[37m▁\x1b[0m\x1b[32m█\x1b[0m",
    ]
    assert exp == res, (exp, res)


def test_gaps() -> None:
    res = sparklines([1, None, 1, 2])
    exp = ["▁ ▁█"]
    assert exp == res
    res = sparklines([1, None, 1])
    exp = ["▄ ▄"]
    assert exp == res, (exp, res)


# ---------------------------------------------------------------------------
# Inverted bars — exercised via auto-split (new public API)
# ---------------------------------------------------------------------------


def test_inverted_basic() -> None:
    # Mixed data: top row = positive bars, bottom row = inverted bars
    res = sparklines([3, 1, 4, 1, 5, 9, 2, -6])
    assert len(res) == 2
    # Bottom row must have ANSI reverse video for the inverted bar
    assert "\x1b[7m" in res[1]
    # The only negative position (index 7) must not be a space in the bottom row
    assert strip_ansi(res[1])[7] != " "
    # All positive positions in the bottom row are spaces
    for i in range(7):
        assert strip_ansi(res[1])[i] == " "


def test_inverted_full_and_empty() -> None:
    # [9, 0, -9]: 9 → full block top; 0 with zero="up" → baseline; -9 → full block bottom
    res = sparklines([9, 0, -9])
    assert len(res) == 2
    top = strip_ansi(res[0])
    bottom = strip_ansi(res[1])
    assert top[0] == "█"  # max positive → full block
    assert top[1] != " "  # zero on positive baseline (zero="up") → non-space
    assert bottom[2] == "█"  # max negative → full block inverted


def test_inverted_gaps() -> None:
    res = sparklines([1, None, -1])
    assert len(res) == 2
    assert strip_ansi(res[0])[1] == " "  # None → space in top row
    assert strip_ansi(res[1])[1] == " "  # None → space in bottom row


def test_inverted_multiline() -> None:
    # num_lines=4: allocate_rows(9, 6, 4) == (2, 2) → 2 up + 2 down = 4 total
    res = sparklines([3, 1, 4, 1, 5, 9, 2, -6], num_lines=4)
    assert len(res) == 4
    # At least one of the bottom two rows must have reverse video
    assert "\x1b[7m" in res[2] or "\x1b[7m" in res[3]


def test_inverted_multiline_row_order() -> None:
    # [1, -9] with num_lines=4: allocate_rows(1, 9, 4) == (1, 3)
    # → 1 up-row + 3 down-rows = 4 total
    res = sparklines([1, -9], num_lines=4)
    assert len(res) == 4
    # Largest negative (-9) fills all three down-rows at position 1
    for row in res[1:]:
        assert strip_ansi(row)[1] == "█"
    # Smallest positive (1) appears only in the single up-row
    assert strip_ansi(res[0])[0] != " "
    assert strip_ansi(res[0])[1] == " "  # position 1 is negative, absent from top


def test_inverted_with_emph() -> None:
    res = sparklines([1, 5, -9], emph=["red:ge:5"])
    assert len(res) == 2
    # Bottom row: -9 → abs → 9, satisfies red:ge:5, full block → colored without
    # reverse video (v==8 path uses force_color=True so ANSI is present regardless of TTY)
    assert "\x1b[" in res[1]


def test_inverted_with_explicit_range() -> None:
    # All-negative data — minimum/maximum ARE respected in the inverted path
    res = sparklines([-1, -100], minimum=0, maximum=100)
    stripped = strip_ansi(res[0])
    # Small value relative to large maximum → tiny bar, not a space
    assert stripped[0] != " "
    # Maximum → full block
    assert stripped[1] == "█"


def test_inverted_no_color_fallback() -> None:
    orig = os.environ.get("NO_COLOR")
    try:
        os.environ["NO_COLOR"] = "1"
        res = sparklines([3, 1, -4, 1, -5, 9, 2, 6])
        assert len(res) == 2
        # No ANSI codes in NO_COLOR mode
        assert "\x1b[" not in res[0]
        assert "\x1b[" not in res[1]
        # Bottom row falls back to top-fill Unicode characters
        assert any(ch in res[1] for ch in "▔▀█")
    finally:
        if orig is None:
            del os.environ["NO_COLOR"]
        else:
            os.environ["NO_COLOR"] = orig


# ---------------------------------------------------------------------------
# Auto-split detection and routing
# ---------------------------------------------------------------------------


def test_auto_split_detected() -> None:
    res = sparklines([3, -1, 4, -2, 5])
    assert len(res) == 2
    top = strip_ansi(res[0])
    bottom = strip_ansi(res[1])
    # Negative positions → spaces in top row
    assert top[1] == " "
    assert top[3] == " "
    # Positive positions → spaces in bottom row
    assert bottom[0] == " "
    assert bottom[2] == " "
    assert bottom[4] == " "


def test_auto_split_all_positive() -> None:
    res = sparklines([1, 2, 3])
    assert len(res) == 1  # no split; single upward row


def test_auto_split_all_negative() -> None:
    res = sparklines([-1, -2, -3])
    assert len(res) == 1  # single inverted row
    assert "\x1b[7m" in res[0]  # reverse video present


def test_auto_split_gaps() -> None:
    res = sparklines([1, None, -1])
    assert len(res) == 2
    assert strip_ansi(res[0])[1] == " "  # None → space in top row
    assert strip_ansi(res[1])[1] == " "  # None → space in bottom row


# ---------------------------------------------------------------------------
# Proportional split table (author's canonical cases)
# ---------------------------------------------------------------------------


def test_proportional_3_3() -> None:
    assert ideal_num_rows(3, 3) == 2
    assert allocate_rows(3, 3, 2) == (1, 1)


def test_proportional_6_3() -> None:
    assert ideal_num_rows(6, 3) == 3
    assert allocate_rows(6, 3, 3) == (2, 1)


def test_proportional_9_3() -> None:
    assert ideal_num_rows(9, 3) == 4
    assert allocate_rows(9, 3, 4) == (3, 1)


def test_proportional_6_4() -> None:
    assert ideal_num_rows(6, 4) == 5
    assert allocate_rows(6, 4, 5) == (3, 2)


# ---------------------------------------------------------------------------
# Author's key worked dataset: [1,2,3,-1,-2,-3,0,4,5,6]
# pos_max=6, neg_max=3
# ---------------------------------------------------------------------------


def test_worked_auto() -> None:
    # ideal_num_rows(6, 3) == 3; allocate_rows(6,3,3) == (2,1) → 2+1=3 rows
    res = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines="auto")
    assert len(res) == 3


def test_worked_integer_n() -> None:
    # allocate_rows(6, 3, 5): size=9, ideal_i=5*6/9=3.33, target_i=3
    # i=3,j=2: imbalance=|6*2-3*3|=|12-9|=3, key=(3,1,0.33,0)
    # i=2,j=3: imbalance=|6*3-3*2|=|18-6|=12, key=(12,1,1.33,1)
    # i=4,j=1: imbalance=|6*1-3*4|=|6-12|=6, key=(6,3,0.67,1)
    # best: (3,2) → 3+2=5 rows
    res = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines=5)
    assert len(res) == 5


def test_worked_tuple_layout() -> None:
    # Explicit (4,5): 4 up + 5 down = 9 rows; per-side scaling
    res = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines=(4, 5))
    assert len(res) == 9


def test_worked_shared_scale() -> None:
    # With auto or integer num_lines, shared max=6 applies to both sides.
    # The single neg bar (neg_max=3) should be roughly half the height of the
    # largest pos bar (pos_max=6) because both are scaled to max=6.
    res_auto = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines="auto")
    res_int = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines=3)
    # Both should produce 3 rows (same allocation for same data)
    assert len(res_auto) == 3
    assert len(res_int) == 3


# ---------------------------------------------------------------------------
# Zero handling
# ---------------------------------------------------------------------------


def test_zero_up() -> None:
    # zero="up" (default): zeros sit on the positive baseline
    res = sparklines([0, 1, 2, -1, -2, 0], zero="up")
    assert len(res) == 2
    top = strip_ansi(res[0])
    bottom = strip_ansi(res[1])
    # Zeros (positions 0 and 5) are non-space in the top row
    assert top[0] != " "
    assert top[5] != " "
    # Zeros are absent from the bottom row
    assert bottom[0] == " "
    assert bottom[5] == " "


def test_zero_none() -> None:
    # zero="none": zeros are gaps on both sides
    res = sparklines([0, 1, 2, -1, -2, 0], zero="none")
    assert len(res) == 2
    top = strip_ansi(res[0])
    bottom = strip_ansi(res[1])
    assert top[0] == " "
    assert top[5] == " "
    assert bottom[0] == " "
    assert bottom[5] == " "


# ---------------------------------------------------------------------------
# Scaling: shared vs per-side
# ---------------------------------------------------------------------------


def test_auto_split_shared_scale() -> None:
    # Equal magnitude: shared scale → both bars are full blocks
    res = sparklines([5, -5])
    assert len(res) == 2
    assert strip_ansi(res[0])[0] == "█"
    assert strip_ansi(res[1])[1] == "█"


def test_auto_split_per_side_scale() -> None:
    # Explicit tuple: each side scaled independently → both bars are full blocks
    res = sparklines([6, -3], num_lines=(1, 1))
    assert len(res) == 2
    assert strip_ansi(res[0])[0] == "█"  # 6/6 = full
    assert strip_ansi(res[1])[1] == "█"  # 3/3 = full (per-side)

    # Contrast: shared scale → bottom bar is half-height, not full
    res_shared = sparklines([6, -3])
    assert strip_ansi(res_shared[1])[1] != "█"  # 3/6 ≠ full with shared max


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_num_lines_auto_cli(capsys: pytest.CaptureFixture[str]) -> None:
    main(["-n", "auto", "1", "2", "3", "-1", "-2", "-3", "0", "4", "5", "6"])
    out, _ = capsys.readouterr()
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 3  # ideal_num_rows(6, 3) == 3


def test_num_lines_tuple_cli(capsys: pytest.CaptureFixture[str]) -> None:
    main(["-n", "4:5", "1", "2", "-1", "-2"])
    out, _ = capsys.readouterr()
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 9  # 4 up + 5 down


def test_zero_flag_cli(capsys: pytest.CaptureFixture[str]) -> None:
    main(["--zero", "none", "0", "1", "-1", "0"])
    out, _ = capsys.readouterr()
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 2
    # Zeros (positions 0 and 3) should be spaces in both rows
    assert strip_ansi(lines[0])[0] == " "
    assert strip_ansi(lines[0])[3] == " "
    assert strip_ansi(lines[1])[0] == " "
    assert strip_ansi(lines[1])[3] == " "


def test_demo_consistency() -> None:
    toplevel = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    with open(os.path.join(toplevel, "tests", "demo-output")) as stream:
        exp = stream.read()
    res = demo([])

    assert strip_ansi(exp) == strip_ansi(res), (
        "Demo output has changed. Verify it and update demo-output!"
    )
    assert "\x1b[7m" in res, "Demo inverted output is missing ANSI reverse video codes"


def test_main_version(capsys: pytest.CaptureFixture[str]) -> None:
    pyproject_toml = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_toml, "rb") as f:
        project_data = tomllib.load(f)
    expected_version = project_data["project"]["version"]

    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0

    out, _ = capsys.readouterr()
    assert out == f"{expected_version}\n"
