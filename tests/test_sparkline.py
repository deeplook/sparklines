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


def test_demo_consistency() -> None:
    toplevel = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    with open(os.path.join(toplevel, "tests", "demo-output")) as stream:
        exp = stream.read()
    res = demo([])

    with open("/tmp/blah", "w") as stream:
        stream.write(res)

    assert exp == res, "Demo output has changed. Verify it and update demo-output!"


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
