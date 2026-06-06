#!/usr/bin/env python

"""
CLI entry point for the program.
"""

import argparse
import importlib.util
import re
import sys
from importlib.metadata import version
from typing import Optional

if sys.version_info.major >= 3:
    from sparklines.sparklines import NumLines, sparklines, demo
else:
    from sparklines import sparklines, demo

HAVE_TERMCOLOR = bool(importlib.util.find_spec("termcolor"))


def _float_or_none(num_str: str) -> Optional[float]:
    """Convert a string to a float if possible or None."""
    try:
        res = float(num_str)
    except ValueError:
        res = None
    return res


def test_valid_number(arg: str) -> str:
    """Argparse validator for input numbers, basically floats or null/none."""
    # https://stackoverflow.com/questions/385558/extract-float-double-value

    # ok if we find (can parse) a float, returning the respective substring
    float_pat = r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
    m = re.search(float_pat, arg)
    if m:
        return m.group(0)

    # ok if we find a 'null' or 'none' string which is then returned
    m = re.search("(null|none)", arg.lower())
    if m:
        return m.group(0)

    # otherwise not ok, making argparse barf
    raise ValueError()


def test_valid_emphasis(arg: str) -> str:
    """Argparse validator for color filter expressions."""
    pat = r"\w+\:(eq|gt|ge|lt|le)\:.+"
    if re.match(pat, arg):
        return arg

    raise ValueError()


def parse_num_lines(arg: str) -> "NumLines":
    """Parse -n argument: integer, 'auto', or 'up:down'."""
    if arg == "auto":
        return "auto"
    if ":" in arg:
        parts = arg.split(":", 1)
        try:
            up, down = int(parts[0]), int(parts[1])
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"invalid row split: {arg!r} (use up:down, e.g. 4:4)"
            )
        if up < 1 or down < 1:
            raise argparse.ArgumentTypeError(
                f"row split must be >= 1 on each side, got {arg!r}"
            )
        return (up, down)
    try:
        n = int(arg)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"invalid row count: {arg!r} (use a positive integer, 'auto', or up:down)"
        )
    if n < 1:
        raise argparse.ArgumentTypeError(f"-n must be >= 1, got {n}")
    return n


def main(argv: Optional[list[str]] = None) -> None:
    """Main entry point for the CLI."""
    desc = """Sparklines on the command-line, e.g. ▃▁▄▁▄█▂▅ for
        3 1 4 1 5 9 2 6. Please add bug reports and suggestions to
        https://github.com/deeplook/sparklines/issues."""
    p = argparse.ArgumentParser(description=desc)

    p.add_argument(
        "-V",
        "--version",
        action="version",
        help="Display version number and quit.",
        version=version("sparklines"),
    )

    help_d = """Show a few usage examples for given (mandatory) input
        values. All other options are ignored."""
    p.add_argument("-d", "--demo", action="store_true", help=help_d)

    p.add_argument(
        "-m", "--min", type=float, help="Use this value as the minimum for scaling."
    )

    p.add_argument(
        "-M", "--max", type=float, help="Use this value as the maximum for scaling."
    )

    help_emph = f"""Emphasize input values below or above a certain
        threshold (e.g. "green:gt:5.0"). This option takes one argument
        value, but can be given repeatedly. Works only when optional
        dependancy "termcolor" is met (which is {HAVE_TERMCOLOR} here). Otherwise
        has no effect."""
    p.add_argument(
        "-e",
        "--emphasize",
        metavar="STRING",
        type=test_valid_emphasis,
        default=[],
        action="append",
        help=help_emph,
    )

    p.add_argument(
        "-n",
        "--num-lines",
        metavar="NUMBER",
        help="rows per sparkline: integer, 'auto', or up:down (e.g. 4:4). Default: 1.",
        default=1,
        type=parse_num_lines,
    )

    p.add_argument(
        "--zero",
        choices=["up", "none"],
        default="up",
        help="how to render 0: 'up' = baseline on positive side (default); 'none' = gap.",
    )

    help_nums = """A positive numeric value >= 0, e.g. 0, 3.14, 2e2.
        Negative numbers are supported. The string values null and None (in any
        spelling) represent empty slots, but not the value 0!"""
    p.add_argument(
        "nums",
        metavar="VALUE",
        type=test_valid_number,
        help=help_nums,
        nargs="*",
        default=sys.stdin,
    )

    help_wrap = """Wrap the graph to a new line after PERIOD
    data points. This is useful for data with natural periodicity:
    for example daily or weekly.
    """
    p.add_argument("-w", "--wrap", metavar="PERIOD", type=int, help=help_wrap)

    a = args = p.parse_args(argv)

    numbers = args.nums
    if numbers == sys.stdin:
        numbers = numbers.read().strip().split()
    numbers = [_float_or_none(n) for n in numbers]

    if args.demo:
        print(demo(numbers))
        sys.exit()

    for line in sparklines(
        numbers,
        num_lines=a.num_lines,
        emph=a.emphasize,
        minimum=a.min,
        maximum=a.max,
        wrap=args.wrap,
        zero=a.zero,
    ):
        print(line)


if __name__ == "__main__":
    main()
