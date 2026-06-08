"""Tests for basic (positive-only) sparkline output."""

from sparklines import sparklines


def test_pi() -> None:
    """Test first eight digits of Pi."""
    res = sparklines([3, 1, 4, 1, 5, 9, 2, 6])
    exp = ["▃▁▄▁▄█▂▅"]
    assert res == exp


def test_minmax() -> None:
    """Test two values, min and max."""
    res = sparklines([1, 8])
    exp = ["▁█"]
    assert res == exp


def test_rounding0() -> None:
    """Test two values, min and max."""
    res = sparklines([1, 5, 8])
    exp = ["▁▅█"]
    assert res == exp


def test_single_value() -> None:
    """Test single values all have the same four pixel high output character."""
    for i in range(10):
        res = sparklines([i])
        exp = ["▄"]
        assert res == exp


def test_empty() -> None:
    """Make sure degenerate cases don't fail."""
    res = sparklines([])
    exp = [""]
    assert res == exp


def test_multiline() -> None:
    """Test multi-line sparkline output with num_lines=3."""
    res = sparklines([1, 5, 8], num_lines=3)
    exp = ["  █", " ▆█", "▁██"]
    assert res == exp


def test_gaps() -> None:
    """Test that None values render as blank spaces in the output."""
    res = sparklines([1, None, 1, 2])
    exp = ["▁ ▁█"]
    assert exp == res
    res = sparklines([1, None, 1])
    exp = ["▄ ▄"]
    assert exp == res, (exp, res)


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
