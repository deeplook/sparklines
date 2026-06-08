"""Tests for line-wrapping behaviour, including mixed positive/negative data."""

from sparklines import sparklines
from tests.helpers import strip_ansi


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


def test_wrap_escaping_consistency() -> None:
    """Test that emphasis ANSI codes don't affect bar characters when stripped."""
    no_emph = sparklines([1, 2, 3, 1, 2, 3, 1, 2], wrap=3)
    stripped_emph = map(
        strip_ansi, sparklines([1, 2, 3, 1, 2, 3, 1, 2], wrap=3, emph=["green:le:1.0"])
    )
    assert no_emph == list(stripped_emph)


def test_wrap_mixed_data() -> None:
    """Test that wrap interleaves pos/neg rows per window, not all-pos then all-neg."""
    res = [strip_ansi(line) for line in sparklines([-4, -5, -6, 1, 2, 3], wrap=3)]
    assert res[0].strip() == ""
    assert res[1].strip() != ""
    assert res[2] == ""
    assert res[3].strip() != ""
    assert res[4].strip() == ""


def test_wrap_mixed_structure() -> None:
    """Test output length: 2 windows × (pos+neg rows) + 1 separator = 5 lines."""
    res = sparklines([-4, -5, -6, 1, 2, 3], wrap=3)
    assert len(res) == 5
    assert res[2] == ""


def test_wrap_mixed_both_sides() -> None:
    """Test wrap when every window contains both positive and negative values."""
    res = [strip_ansi(line) for line in sparklines([1, -1, 2, -2], wrap=2)]
    assert len(res) == 5
    for win_start in (0, 3):
        assert res[win_start].strip() != ""
        assert res[win_start + 1].strip() != ""


def test_wrap_mixed_shared_scale() -> None:
    """Test that pos/neg scale is global across all wrap windows."""
    # [-1, 1, -8, 8] with wrap=2: global shared scale = 8.
    # Window 0 has small values; window 1 has the maximum.
    # With per-window scale both windows look identical; global scale makes them differ.
    res = [strip_ansi(line) for line in sparklines([-1, 1, -8, 8], wrap=2)]
    assert len(res) == 5
    assert res[0].strip() != ""
    assert res[3].strip() != ""
    assert res[3] > res[0]


def test_wrap_mixed_num_lines_tuple() -> None:
    """Test wrap with explicit up:down row allocation."""
    res = [
        strip_ansi(line)
        for line in sparklines([-4, -5, -6, 1, 2, 3], wrap=3, num_lines=(1, 2))
    ]
    assert len(res) == 7
    assert res[3] == ""


def test_wrap_all_negative_unaffected() -> None:
    """Test that wrap on all-negative data (not mixed) still works correctly."""
    res = [strip_ansi(line) for line in sparklines([-1, -2, -3, -4], wrap=2)]
    assert len(res) == 3
    assert res[1] == ""
