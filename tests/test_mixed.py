"""Tests for mixed positive/negative data.

Covers inverted bars, auto-split, row allocation, zero handling, and scaling.
"""

import math
import os


from sparklines import sparklines
from sparklines.sparklines import allocate_rows, ideal_num_rows
from tests.helpers import strip_ansi


# ---------------------------------------------------------------------------
# Inverted bars
# ---------------------------------------------------------------------------


def test_inverted_basic() -> None:
    """Test that mixed data produces two rows: upward positives, inverted negatives."""
    res = sparklines([3, 1, 4, 1, 5, 9, 2, -6])
    assert len(res) == 2
    assert "\x1b[7m" in res[1]
    assert strip_ansi(res[1])[7] != " "
    for i in range(7):
        assert strip_ansi(res[1])[i] == " "


def test_inverted_full_and_empty() -> None:
    """Test full positive block, zero baseline, and full inverted block."""
    res = sparklines([9, 0, -9])
    assert len(res) == 2
    top = strip_ansi(res[0])
    bottom = strip_ansi(res[1])
    assert top[0] == "█"
    assert top[1] != " "
    assert bottom[2] == "█"


def test_inverted_gaps() -> None:
    """Test that None values produce spaces in both the positive and inverted rows."""
    res = sparklines([1, None, -1])
    assert len(res) == 2
    assert strip_ansi(res[0])[1] == " "
    assert strip_ansi(res[1])[1] == " "


def test_inverted_multiline() -> None:
    """Test that num_lines=4 allocates rows proportionally across pos and neg."""
    res = sparklines([3, 1, 4, 1, 5, 9, 2, -6], num_lines=4)
    assert len(res) == 4
    assert "\x1b[7m" in res[2] or "\x1b[7m" in res[3]


def test_inverted_multiline_row_order() -> None:
    """Test that rows are ordered correctly with more down-rows than up-rows."""
    res = sparklines([1, -9], num_lines=4)
    assert len(res) == 4
    for row in res[1:]:
        assert strip_ansi(row)[1] == "█"
    assert strip_ansi(res[0])[0] != " "
    assert strip_ansi(res[0])[1] == " "


def test_inverted_with_explicit_range() -> None:
    """Test that explicit minimum/maximum are respected for all-negative data."""
    res = sparklines([-1, -100], minimum=0, maximum=100)
    stripped = strip_ansi(res[0])
    assert stripped[0] != " "
    assert stripped[1] == "█"


def test_inverted_no_color_fallback() -> None:
    """Test that NO_COLOR suppresses ANSI and falls back to top-fill Unicode chars."""
    orig = os.environ.get("NO_COLOR")
    try:
        os.environ["NO_COLOR"] = "1"
        res = sparklines([3, 1, -4, 1, -5, 9, 2, 6])
        assert len(res) == 2
        assert "\x1b[" not in res[0]
        assert "\x1b[" not in res[1]
        assert any(ch in res[1] for ch in "▔▀█")
    finally:
        if orig is None:
            del os.environ["NO_COLOR"]
        else:
            os.environ["NO_COLOR"] = orig


# ---------------------------------------------------------------------------
# Auto-split detection
# ---------------------------------------------------------------------------


def test_auto_split_detected() -> None:
    """Test that mixed positive/negative data is automatically split into two rows."""
    res = sparklines([3, -1, 4, -2, 5])
    assert len(res) == 2
    top = strip_ansi(res[0])
    bottom = strip_ansi(res[1])
    assert top[1] == " "
    assert top[3] == " "
    assert bottom[0] == " "
    assert bottom[2] == " "
    assert bottom[4] == " "


def test_auto_split_all_positive() -> None:
    """Test that all-positive data produces a single upward row with no split."""
    res = sparklines([1, 2, 3])
    assert len(res) == 1


def test_auto_split_all_negative() -> None:
    """Test that all-negative data produces a single inverted row with reverse video."""
    res = sparklines([-1, -2, -3])
    assert len(res) == 1
    assert "\x1b[7m" in res[0]


def test_auto_split_gaps() -> None:
    """Test that None values produce spaces in both rows of a split sparkline."""
    res = sparklines([1, None, -1])
    assert len(res) == 2
    assert strip_ansi(res[0])[1] == " "
    assert strip_ansi(res[1])[1] == " "


# ---------------------------------------------------------------------------
# Proportional row allocation
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
# Key worked dataset: [1,2,3,-1,-2,-3,0,4,5,6]  pos_max=6, neg_max=3
# ---------------------------------------------------------------------------


def test_worked_auto() -> None:
    """Test num_lines='auto' on the key dataset gives 3 rows (2 up + 1 down)."""
    res = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines="auto")
    assert len(res) == 3


def test_worked_integer_n() -> None:
    """Test integer num_lines=5 allocates 3 up + 2 down on the key dataset."""
    res = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines=5)
    assert len(res) == 5


def test_worked_tuple_layout() -> None:
    """Test explicit (4, 5) tuple layout gives 9 rows with per-side scaling."""
    res = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines=(4, 5))
    assert len(res) == 9


def test_worked_shared_scale() -> None:
    """Test that auto and integer num_lines use a shared scale on the key dataset."""
    res_auto = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines="auto")
    res_int = sparklines([1, 2, 3, -1, -2, -3, 0, 4, 5, 6], num_lines=3)
    assert len(res_auto) == 3
    assert len(res_int) == 3


def test_auto_irrational_ratio() -> None:
    """Test that irrational pos/neg ratios fall back gracefully without raising."""
    res = sparklines([1, -(math.sqrt(2))], num_lines="auto")
    assert 2 <= len(res) <= 10


# ---------------------------------------------------------------------------
# Zero handling
# ---------------------------------------------------------------------------


def test_zero_up() -> None:
    """Test that zero='up' renders zeros on the positive baseline."""
    res = sparklines([0, 1, 2, -1, -2, 0], zero="up")
    assert len(res) == 2
    top = strip_ansi(res[0])
    bottom = strip_ansi(res[1])
    assert top[0] != " "
    assert top[5] != " "
    assert bottom[0] == " "
    assert bottom[5] == " "


def test_zero_none() -> None:
    """Test that zero='none' renders zeros as gaps on both positive and negative."""
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
    res = sparklines([5, -5])
    assert len(res) == 2
    assert strip_ansi(res[0])[0] == "█"
    assert strip_ansi(res[1])[1] == "█"


def test_auto_split_per_side_scale() -> None:
    """Test that tuple num_lines uses per-side scaling so each side reaches full."""
    res = sparklines([6, -3], num_lines=(1, 1))
    assert len(res) == 2
    assert strip_ansi(res[0])[0] == "█"
    assert strip_ansi(res[1])[1] == "█"

    res_shared = sparklines([6, -3])
    assert strip_ansi(res_shared[1])[1] != "█"
