"""Tests for colour emphasis: value-based and index-slice expressions."""

from typing import Optional

import pytest

from sparklines import sparklines
from sparklines.sparklines import _check_emphasis


def test_inverted_with_emph() -> None:
    """Test that colour emphasis applies correctly to inverted bars."""
    res = sparklines([1, 5, -9], emph=["red:ge:5"])
    assert len(res) == 2
    # -9 does not satisfy red:ge:5 against original values → no ANSI in neg row
    assert "\x1b[" not in res[1]


def test_emph_by_index_slice() -> None:
    """Test emphasis by index slice: range, step, negative index, empty, bare."""
    data = [1.0, 2.0, 3.0, 4.0, 5.0]

    assert _check_emphasis(data, ["red:[1:3]"]) == {1: "red", 2: "red"}
    assert _check_emphasis(data, ["blue:[::2]"]) == {0: "blue", 2: "blue", 4: "blue"}
    assert _check_emphasis(data, ["green:[-1:]"]) == {4: "green"}
    assert _check_emphasis(data, ["yellow:[2:3]"]) == {2: "yellow"}
    assert _check_emphasis(data, ["red:[5:3]"]) == {}
    assert _check_emphasis(data, ["red:[:]"]) == {i: "red" for i in range(5)}


def test_emph_by_index_skips_none() -> None:
    """Test that index-slice emphasis skips None gaps."""
    data: list[Optional[float]] = [1.0, None, 3.0]
    assert _check_emphasis(data, ["red:[:]"]) == {0: "red", 2: "red"}


def test_emph_by_index_and_value_combined() -> None:
    """Test that index-slice and value expressions can be combined."""
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = _check_emphasis(data, ["red:[0:2]", "blue:ge:4"])
    assert result == {0: "red", 1: "red", 3: "blue", 4: "blue"}


def test_emph_by_index_last_wins() -> None:
    """Test that when two expressions match the same index, the last one wins."""
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
