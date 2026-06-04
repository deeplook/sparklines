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


def test_inverted_basic() -> None:
    res = sparklines([3, 1, 4, 1, 5, 9, 2, 6], inverted=True)
    assert len(res) == 1
    # ANSI reverse video codes must be present for non-full-block chars
    assert "\x1b[7m" in res[0]
    # Full block (max value 9) needs no reverse video
    assert "█" in res[0]
    # Stripped of ANSI the chars are the complement upward block characters
    stripped = strip_ansi(res[0])
    assert stripped == "▅▇▄▇▄█▆▃"


def test_inverted_full_and_empty() -> None:
    res = sparklines([9, 0, 9], inverted=True)
    stripped = strip_ansi(res[0])
    # Max value (9) → full block
    assert stripped[0] == "█"
    assert stripped[2] == "█"
    # Input 0 is not None, so scale_values maps it to min_index=1 — a tiny bar, not a space
    assert stripped[1] != " "


def test_inverted_gaps() -> None:
    res = sparklines([1, None, 1, 2], inverted=True)
    stripped = strip_ansi(res[0])
    assert stripped[1] == " "


def test_inverted_multiline() -> None:
    res = sparklines([3, 1, 4, 1, 5, 9, 2, 6], num_lines=2, inverted=True)
    assert len(res) == 2
    # Top row contains the base portion of all bars
    assert "\x1b[7m" in res[0]
    # Bottom row contains only the overflow of taller bars
    stripped_top = strip_ansi(res[0])
    stripped_bottom = strip_ansi(res[1])
    # Top row has content for every position (no leading spaces)
    assert stripped_top[0] != " "
    # Bottom row is mostly spaces (only tallest values overflow)
    assert stripped_bottom.count(" ") > len(stripped_bottom) // 2


def test_inverted_multiline_row_order() -> None:
    # Tallest value should produce full blocks in both rows;
    # shortest value should appear only in the top row.
    res = sparklines([1, 9], num_lines=2, inverted=True)
    top = strip_ansi(res[0])
    bottom = strip_ansi(res[1])
    # Value 9 (max) fills both rows completely
    assert top[1] == "█"
    assert bottom[1] == "█"
    # Value 1 (min) appears only in top row; bottom row position is space
    assert top[0] != " "
    assert bottom[0] == " "


def test_inverted_with_emph() -> None:
    res = sparklines([1, 5, 9], inverted=True, emph=["red:ge:5"])
    assert len(res) == 1
    # ANSI codes present (both color and reverse video)
    assert "\x1b[" in res[0]
    # Full-block emphasized bar uses the emphasis color directly — no reverse video
    # Use explicit range so value 9 maps to height 8 (not the dv==0 mid-height path)
    full_block_res = sparklines(
        [9], inverted=True, emph=["red:ge:1"], minimum=0, maximum=9
    )
    assert "\x1b[" in full_block_res[0]
    assert "\x1b[7m" not in full_block_res[0]


def test_inverted_with_explicit_range() -> None:
    res = sparklines([1, 100], inverted=True, minimum=0, maximum=100)
    stripped = strip_ansi(res[0])
    # Small value relative to large maximum → tiny bar, not a space
    assert stripped[0] != " "
    # Maximum → full block
    assert stripped[1] == "█"


def test_inverted_negative_autoabs() -> None:
    # Negatives are silently abs()'d; largest magnitude → full block
    res = sparklines([-9, -1], inverted=True)
    assert len(res) == 1
    stripped = strip_ansi(res[0])
    assert stripped[0] == "█"
    assert stripped[1] != " "


def test_inverted_no_color_fallback() -> None:
    orig = os.environ.get("NO_COLOR")
    try:
        os.environ["NO_COLOR"] = "1"
        res = sparklines([3, 1, 4, 1, 5, 9, 2, 6], inverted=True)
        # No ANSI codes in NO_COLOR mode
        assert "\x1b[" not in res[0]
        # Falls back to top-fill Unicode characters
        assert any(ch in res[0] for ch in "▔▀█")
    finally:
        if orig is None:
            del os.environ["NO_COLOR"]
        else:
            os.environ["NO_COLOR"] = orig


def test_inverted_cli(capsys: pytest.CaptureFixture[str]) -> None:
    main(["-i", "3", "1", "4", "1", "5", "9", "2", "6"])
    out, _ = capsys.readouterr()
    assert "\x1b[7m" in out


def test_demo_consistency() -> None:
    toplevel = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    with open(os.path.join(toplevel, "tests", "demo-output")) as stream:
        exp = stream.read()
    res = demo([])

    assert strip_ansi(exp) == strip_ansi(res), (
        "Demo output has changed. Verify it and update demo-output!"
    )
    assert "\x1b[7m" in res, "Demo inverted output is missing ANSI reverse video codes"


def test_split_basic() -> None:
    res = sparklines([3, -1, 4, -2, 5], split=True)
    assert len(res) == 2
    top_stripped = strip_ansi(res[0])
    bottom_stripped = strip_ansi(res[1])
    # Negative positions → None in pos → spaces in top row
    assert top_stripped[1] == " "
    assert top_stripped[3] == " "
    # Positive positions → None in neg → spaces in bottom row
    assert bottom_stripped[0] == " "
    assert bottom_stripped[2] == " "
    assert bottom_stripped[4] == " "


def test_split_shared_scale() -> None:
    res = sparklines([5, -5], split=True)
    top_stripped = strip_ansi(res[0])
    bottom_stripped = strip_ansi(res[1])
    # Equal magnitude → equal-height bars (both full blocks)
    assert top_stripped[0] == "█"
    assert bottom_stripped[1] == "█"


def test_split_all_positive() -> None:
    res = sparklines([1, 2, 3], split=True)
    assert len(res) == 2
    # No negatives → bottom row is all spaces
    assert res[1] == "   "


def test_split_all_negative() -> None:
    res = sparklines([-1, -2, -3], split=True)
    assert len(res) == 2
    # No positives → top row is all spaces
    assert res[0] == "   "


def test_split_gaps() -> None:
    res = sparklines([1, None, -1], split=True)
    assert len(res) == 2
    # None passes through to both rows as spaces
    assert strip_ansi(res[0])[1] == " "
    assert strip_ansi(res[1])[1] == " "


def test_split_cli(capsys: pytest.CaptureFixture[str]) -> None:
    main(["-s", "3", "-1", "4", "-2", "5"])
    out, _ = capsys.readouterr()
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 2


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
