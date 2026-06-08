"""Tests for scale_values and batch."""

from sparklines import batch, scale_values


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


def test_scale_pi() -> None:
    """Test scale Pi."""
    res = scale_values([3, 1, 4, 1, 5, 9, 2, 6])
    exp = [3, 1, 4, 1, 4, 8, 2, 5]
    assert res == exp


def test_batch() -> None:
    """Test batch splitting with and without a batch size."""
    batches = batch(3, range(10))
    assert batches == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]], batches

    batches = batch(None, range(3))
    assert batches == [[0, 1, 2]]
