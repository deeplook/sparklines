"""Tests for the CLI: argument parsing, --version, --demo, and integration."""

import os
import sys
from pathlib import Path

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from sparklines import demo
from sparklines.__main__ import main
from sparklines.__main__ import test_valid_number as is_valid_number
from tests.helpers import strip_ansi


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


def test_num_lines_auto_cli(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that -n auto produces the correct row count via the CLI."""
    main(["-n", "auto", "1", "2", "3", "-1", "-2", "-3", "0", "4", "5", "6"])
    out, _ = capsys.readouterr()
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 3


def test_num_lines_tuple_cli(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that -n up:down produces the correct total row count via the CLI."""
    main(["-n", "4:5", "1", "2", "-1", "-2"])
    out, _ = capsys.readouterr()
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 9


def test_zero_flag_cli(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that --zero none renders zeros as gaps in both rows via the CLI."""
    main(["--zero", "none", "0", "1", "-1", "0"])
    out, _ = capsys.readouterr()
    lines = out.rstrip("\n").split("\n")
    assert len(lines) == 2
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
