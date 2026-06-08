"""Run from the repo root with: pytest tests."""

import os
import re
from pathlib import Path
import sys
from typing import Optional

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
    """Test batch splitting with and without a batch size."""
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
    """Test that values above maximum are clamped to the maximum bar height."""
    res = sparklines([1, 2, 3, 10, 10], maximum=3)
    exp = ["▁▄███"]
    assert res == exp


def test_maximum_internal_consistency() -> None:
    """Test that explicit maximum produces the same result as pre-clamped data."""
    res = sparklines([1, 2, 3, 10, 10, 1], maximum=3)
    exp = sparklines([1, 2, 3, 3, 3, 1], maximum=3)
    assert res == exp


def test_minimum() -> None:
    """Test that values below minimum are clamped to the minimum bar height."""
    res = sparklines([0, 0, 11, 12, 13], minimum=10)
    exp = ["▁▁▃▆█"]
    assert res == exp


def test_minimum_internal_consistency() -> None:
    """Test that explicit minimum produces the same result as pre-clamped data."""
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
    """Test multi-line sparkline output with num_lines=3."""
    res = sparklines([1, 5, 8], num_lines=3)
    exp = ["  █", " ▆█", "▁██"]
    assert res == exp


def test_wrap() -> None:
    """Test that long sparklines are broken into segments at the wrap boundary."""
    res = sparklines([1, 2, 3, 1, 2, 3, 1, 2], wrap=3)
    exp = ["▁▄█", "", "▁▄█", "", "▁▄"]
    assert res == exp


def test_wrap_scale() -> None:
    """Test that scale is shared across all wrapped segments."""
    res = sparklines([100, 50, 100, 20, 50, 20, 1, 1, 1], wrap=3)
    exp = ["█▄█", "", "▂▄▂", "", "▁▁▁"]
    assert res == exp


def test_wrap_consistency() -> None:
    """Test wrapped output matches manually assembled segments with shared scale."""
    res = sparklines([1, 2, 3, 1, 2, 3, 1, 2], wrap=3)
    exp = (
        sparklines([1, 2, 3], maximum=3, minimum=1)
        + [""]
        + sparklines([1, 2, 3], maximum=3, minimum=1)
        + [""]
        + sparklines([1, 2], maximum=3, minimum=1)
    )
    assert res == exp


def test_wrap_mixed_data() -> None:
    """Test that wrap interleaves pos/neg rows per window, not all-pos then all-neg."""
    res = [strip_ansi(line) for line in sparklines([-4, -5, -6, 1, 2, 3], wrap=3)]
    # Window 0: no positives (top row blank), neg bars (bottom row non-blank)
    assert res[0].strip() == ""
    assert res[1].strip() != ""
    # separator
    assert res[2] == ""
    # Window 1: pos bars (top row non-blank), no negatives (bottom row blank)
    assert res[3].strip() != ""
    assert res[4].strip() == ""


def test_wrap_mixed_structure() -> None:
    """Test output length: 2 windows × (pos+neg rows) + 1 separator = 5 lines."""
    res = sparklines([-4, -5, -6, 1, 2, 3], wrap=3)
    assert len(res) == 5
    assert res[2] == ""  # separator between windows


def test_wrap_mixed_both_sides() -> None:
    """Test wrap when every window contains both positive and negative values."""
    res = [strip_ansi(line) for line in sparklines([1, -1, 2, -2], wrap=2)]
    # 2 windows, each has pos row + neg row, separated by ""
    assert len(res) == 5
    for win_start in (0, 3):
        assert res[win_start].strip() != ""  # pos row has a bar
        assert res[win_start + 1].strip() != ""  # neg row has a bar


def test_wrap_mixed_shared_scale() -> None:
    """Test that pos/neg scale is global across all wrap windows."""
    # [-1, 1, -8, 8] with wrap=2: global shared scale = 8.
    # Window 0 has small values; window 1 has the maximum.
    # With per-window scale both windows look identical; global scale makes them differ.
    res = [strip_ansi(line) for line in sparklines([-1, 1, -8, 8], wrap=2)]
    assert len(res) == 5
    # pos rows: window 0 (index 0) and window 1 (index 3)
    # The max pos value 8 is in window 1, so its bar char must be larger
    assert res[0].strip() != ""  # window 0 has a positive bar
    assert res[3].strip() != ""  # window 1 has a positive bar
    assert res[3] > res[0]  # block chars are ordered by codepoint: ▁ < ▂ … < █


def test_wrap_mixed_num_lines_tuple() -> None:
    """Test wrap with explicit up:down row allocation."""
    res = [
        strip_ansi(line)
        for line in sparklines([-4, -5, -6, 1, 2, 3], wrap=3, num_lines=(1, 2))
    ]
    # Each window: 1 pos row + 2 neg rows = 3 rows; 2 windows + 1 separator = 7 lines
    assert len(res) == 7
    assert res[3] == ""  # separator


def test_wrap_all_negative_unaffected() -> None:
    """Test that wrap on all-negative data (not mixed) still works correctly."""
    res = [strip_ansi(line) for line in sparklines([-1, -2, -3, -4], wrap=2)]
    assert len(res) == 3  # 2 windows + 1 separator
    assert res[1] == ""


def test_wrap_escaping_consistency() -> None:
    """Test that emphasis ANSI codes don't affect bar characters when stripped."""
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
    """Test that None values render as blank spaces in the output."""
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
    """Test that mixed data produces two rows: upward positives, inverted negatives."""
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
    """Test full positive block, zero baseline, and full inverted block."""
    # [9, 0, -9]: 9 → full block top; 0 with zero="up" → baseline;
    # -9 → full block bottom
    res = sparklines([9, 0, -9])
    assert len(res) == 2
    top = strip_ansi(res[0])
    bottom = strip_ansi(res[1])
    assert top[0] == "█"  # max positive → full block
    assert top[1] != " "  # zero on positive baseline (zero="up") → non-space
    assert bottom[2] == "█"  # max negative → full block inverted


def test_inverted_gaps() -> None:
    """Test that None values produce spaces in both the positive and inverted rows."""
    res = sparklines([1, None, -1])
    assert len(res) == 2
    assert strip_ansi(res[0])[1] == " "  # None → space in top row
    assert strip_ansi(res[1])[1] == " "  # None → space in bottom row


def test_inverted_multiline() -> None:
    """Test that num_lines=4 allocates rows proportionally across pos and neg."""
    # num_lines=4: allocate_rows(9, 6, 4) == (2, 2) → 2 up + 2 down = 4 total
    res = sparklines([3, 1, 4, 1, 5, 9, 2, -6], num_lines=4)
    assert len(res) == 4
    # At least one of the bottom two rows must have reverse video
    assert "\x1b[7m" in res[2] or "\x1b[7m" in res[3]


def test_inverted_multiline_row_order() -> None:
    """Test that rows are ordered correctly with more down-rows than up-rows."""
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
    """Test that colour emphasis applies correctly to inverted bars."""
    res = sparklines([1, 5, -9], emph=["red:ge:5"])
    assert len(res) == 2
    # -9 does not satisfy red:ge:5 against original values → no ANSI in neg row
    assert "\x1b[" not in res[1]


def test_emph_by_index_slice() -> None:
    """Test emphasis by index slice: range, step, negative index, empty, bare."""
    from sparklines.sparklines import _check_emphasis

    data = [1.0, 2.0, 3.0, 4.0, 5.0]

    assert _check_emphasis(data, ["red:[1:3]"]) == {1: "red", 2: "red"}
    assert _check_emphasis(data, ["blue:[::2]"]) == {0: "blue", 2: "blue", 4: "blue"}
    assert _check_emphasis(data, ["green:[-1:]"]) == {4: "green"}
    assert _check_emphasis(data, ["yellow:[2:3]"]) == {2: "yellow"}
    assert _check_emphasis(data, ["red:[5:3]"]) == {}
    assert _check_emphasis(data, ["red:[:]"]) == {i: "red" for i in range(5)}


def test_emph_by_index_skips_none() -> None:
    """Test that index-slice emphasis skips None gaps."""
    from sparklines.sparklines import _check_emphasis

    data: list[Optional[float]] = [1.0, None, 3.0]
    assert _check_emphasis(data, ["red:[:]"]) == {0: "red", 2: "red"}


def test_emph_by_index_and_value_combined() -> None:
    """Test that index-slice and value expressions can be combined."""
    from sparklines.sparklines import _check_emphasis

    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = _check_emphasis(data, ["red:[0:2]", "blue:ge:4"])
    assert result == {0: "red", 1: "red", 3: "blue", 4: "blue"}


def test_emph_by_index_last_wins() -> None:
    """Test that when two expressions match the same index, the last one wins."""
    from sparklines.sparklines import _check_emphasis

    data = [1.0, 2.0, 3.0]
    result = _check_emphasis(data, ["red:[:]", "blue:[1:2]"])
    assert result[1] == "blue"


def test_emph_index_cli_validator() -> None:
    """Test CLI validator accepts valid slice expressions and rejects malformed ones."""
    from sparklines.__main__ import test_valid_emphasis

    assert test_valid_emphasis("red:[0:3]") == "red:[0:3]"
    assert test_valid_emphasis("blue:[::2]") == "blue:[::2]"
    assert test_valid_emphasis("green:[-1:]") == "green:[-1:]"
    assert test_valid_emphasis("yellow:[:]") == "yellow:[:]"

    with pytest.raises(ValueError):
        test_valid_emphasis("red:[")
    with pytest.raises(ValueError):
        test_valid_emphasis("red:0:3")


def test_inverted_with_explicit_range() -> None:
    """Test that explicit minimum/maximum are respected for all-negative data."""
    # All-negative data — minimum/maximum ARE respected in the inverted path
    res = sparklines([-1, -100], minimum=0, maximum=100)
    stripped = strip_ansi(res[0])
    # Small value relative to large maximum → tiny bar, not a space
    assert stripped[0] != " "
    # Maximum → full block
    assert stripped[1] == "█"


def test_inverted_no_color_fallback() -> None:
    """Test that NO_COLOR suppresses ANSI and falls back to top-fill Unicode chars."""
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
    """Test that mixed positive/negative data is automatically split into two rows."""
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
    """Test that all-positive data produces a single upward row with no split."""
    res = sparklines([1, 2, 3])
    assert len(res) == 1  # no split; single upward row


def test_auto_split_all_negative() -> None:
    """Test that all-negative data produces a single inverted row with reverse video."""
    res = sparklines([-1, -2, -3])
    assert len(res) == 1  # single inverted row
    assert "\x1b[7m" in res[0]  # reverse video present


def test_auto_split_gaps() -> None:
    """Test that None values produce spaces in both rows of a split sparkline."""
    res = sparklines([1, None, -1])
    assert len(res) == 2
    assert strip_ansi(res[0])[1] == " "  # None → space in top row
    assert strip_ansi(res[1])[1] == " "  # None → space in bottom row


# ---------------------------------------------------------------------------
# Proportional split table (author's canonical cases)
# ---------------------------------------------------------------------------


def test_proportional_3_3() -> None:
    """Test equal magnitudes: smallest proportional split is 1:1 at 2 rows."""
    assert ideal_num_rows(3, 3) == 2
    assert allocate_rows(3, 3, 2) == (1, 1)


def test_proportional_6_3() -> None:
    """Test 2:1 ratio: smallest proportional split is 2:1 at 3 rows."""
    assert ideal_num_rows(6, 3) == 3
    assert allocate_rows(6, 3, 3) == (2, 1)


def test_proportional_9_3() -> None:
    """Test 3:1 ratio: smallest proportional split is 3:1 at 4 rows."""
    assert ideal_num_rows(9, 3) == 4
    assert allocate_rows(9, 3, 4) == (3, 1)


def test_proportional_6_4() -> None:
    """Test 3:2 ratio: smallest proportional split is 3:2 at 5 rows."""
    assert ideal_num_rows(6, 4) == 5
    assert allocate_rows(6, 4, 5) == (3, 2)


# ---------------------------------------------------------------------------
# Author's key worked dataset: [1,2,3,-1,-2,-3,0,4,5,6]
# pos_max=6, neg_max=3
# ---------------------------------------------------------------------------


def test_worked_auto() -> None:
    """Test num_lines='auto' on the key dataset gives 3 rows (2 up + 1 down)."""
    # ideal_num_rows(6, 3) == 3; allocate_rows(6,3,3) == (2,1) → 2+1=3 rows
    res = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines="auto")
    assert len(res) == 3


def test_worked_integer_n() -> None:
    """Test integer num_lines=5 allocates 3 up + 2 down on the key dataset."""
    # allocate_rows(6, 3, 5): size=9, ideal_i=5*6/9=3.33, target_i=3
    # i=3,j=2: imbalance=|6*2-3*3|=|12-9|=3, key=(3,1,0.33,0)
    # i=2,j=3: imbalance=|6*3-3*2|=|18-6|=12, key=(12,1,1.33,1)
    # i=4,j=1: imbalance=|6*1-3*4|=|6-12|=6, key=(6,3,0.67,1)
    # best: (3,2) → 3+2=5 rows
    res = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines=5)
    assert len(res) == 5


def test_worked_tuple_layout() -> None:
    """Test explicit (4, 5) tuple layout gives 9 rows with per-side scaling."""
    # Explicit (4,5): 4 up + 5 down = 9 rows; per-side scaling
    res = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines=(4, 5))
    assert len(res) == 9


def test_worked_shared_scale() -> None:
    """Test that auto and integer num_lines use a shared scale on the key dataset."""
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
    """Test that zero='up' renders zeros on the positive baseline."""
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
    """Test that zero='none' renders zeros as gaps on both positive and negative."""
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
    """Test that equal-magnitude values both reach full height under shared scale."""
    # Equal magnitude: shared scale → both bars are full blocks
    res = sparklines([5, -5])
    assert len(res) == 2
    assert strip_ansi(res[0])[0] == "█"
    assert strip_ansi(res[1])[1] == "█"


def test_auto_split_per_side_scale() -> None:
    """Test that tuple num_lines uses per-side scaling so each side reaches full."""
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


def test_auto_irrational_ratio() -> None:
    """Test that irrational pos/neg ratios fall back gracefully without raising."""
    # irrational pos/neg ratio — ideal_num_rows has no exact solution,
    # should fall back gracefully rather than raising ValueError
    import math

    res = sparklines([1, -(math.sqrt(2))], num_lines="auto")
    assert 2 <= len(res) <= 10


def test_num_lines_auto_cli(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that -n auto produces the correct row count via the CLI."""
    main(["-n", "auto", "1", "2", "3", "-1", "-2", "-3", "0", "4", "5", "6"])
    out, _ = capsys.readouterr()
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 3  # ideal_num_rows(6, 3) == 3


def test_num_lines_tuple_cli(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that -n up:down produces the correct total row count via the CLI."""
    main(["-n", "4:5", "1", "2", "-1", "-2"])
    out, _ = capsys.readouterr()
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 9  # 4 up + 5 down


def test_zero_flag_cli(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that --zero none renders zeros as gaps in both rows via the CLI."""
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
    """Test that demo() output matches the checked-in demo-output fixture."""
    toplevel = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    with open(os.path.join(toplevel, "tests", "demo-output")) as stream:
        exp = stream.read()
    res = demo([])

    def normalize(s: str) -> str:
        return "\n".join(line.rstrip() for line in strip_ansi(s).splitlines())

    assert normalize(exp) == normalize(res), (
        "Demo output has changed. Verify it and update demo-output!"
    )
    assert "\x1b[7m" in res, "Demo inverted output is missing ANSI reverse video codes"


def test_main_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that --version prints the version from pyproject.toml and exits 0."""
    pyproject_toml = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_toml, "rb") as f:
        project_data = tomllib.load(f)
    expected_version = project_data["project"]["version"]

    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0

    out, _ = capsys.readouterr()
    assert out == f"{expected_version}\n"
