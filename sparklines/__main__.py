#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CLI entry point for the program.
"""

from __future__ import unicode_literals, print_function
import re
import sys
import argparse

# handle different file types in Python 2 and 3
try:
    import io
    file = io.IOBase
except ImportError:
    pass

try:
    import termcolor
    HAVE_TERMCOLOR = True
except ImportError:
    HAVE_TERMCOLOR = False

if sys.version_info.major >= 3:
    from sparklines.sparklines import sparklines, demo, __version__
else:
    from sparklines import sparklines, demo, __version__


def _float_or_none(num_str):
    "Convert a string to a float if possible or None."

    try:
        res = float(num_str)
    except ValueError:
        res = None
    return res


def test_valid_number(arg):
    "Argparse validator for input numbers, basically floats or null/none."
    # https://stackoverflow.com/questions/385558/extract-float-double-value

    # ok if we find (can parse) a float, returning the respective substring
    float_pat = r'[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
    m = re.search(float_pat, arg)
    if m:
        return m.group(0)

    # ok if we find a 'null' or 'none' string which is then returned
    m = re.search('(null|none)', arg.lower())
    if m:
        return m.group(0)

    # otherwise not ok, making argparse barf
    raise ValueError()


def test_valid_emphasis(arg):
    "Argparse validator for color filter expressions."

    pat = '\w+\:(eq|gt|ge|lt|le)\:.+'
    if re.match(pat, arg):
        return arg
    else:
        raise ValueError()


def main():
    desc = "Sparklines on the command-line, e.g. ▃▁▄▁▄█▂▅ for 3 1 4 1 5 9 2 6."
    p = argparse.ArgumentParser(description=desc)

    p.add_argument('-v', '--verbose', action='store_true',
        help='Provide more verbose (debugging) output (none for now).')

    p.add_argument('-V', '--version', action='store_true',
        help='Display version number and quit.')

    p.add_argument('-d', '--demo', action='store_true',
        help='Show a few usage examples for given (mandatory) input values.')

    help_emph = '''Emphasise input values below or above a certain
        threshold (e.g. "green:gt:5.0"). Works only when optional
        dependancy "termcolor" is met (which is %s here).
        Otherwise has no effect.''' % HAVE_TERMCOLOR
    p.add_argument('-e', '--emphasise', metavar='STRING',
        type=test_valid_emphasis, nargs='+',
        help=help_emph)

    help_n = '''The number of lines for one sparkline (higher numbers
        increase the resolution). An integer >= 1 (default: 1).'''
    p.add_argument('-n', '--num-lines', metavar='NUMBER',
        help=help_n, default='1', type=int)

    help_nums = '''A positive numeric value >= 0, e.g. 0, 3.14, 2e2.
        Negative numbers work, too, but will give unexpected results
        and raise a warning. The string values null and None (in any
        spelling) represent empty slots, but not the value 0!'''
    p.add_argument('nums', metavar='VALUE', type=test_valid_number,
        help=help_nums, nargs='*', default=sys.stdin)

    a = args = p.parse_args()

    if args.version:
        print(__version__)
        sys.exit()

    numbers = args.nums
    if numbers == sys.stdin:
        numbers = numbers.read().strip().split()
    numbers = [_float_or_none(n) for n in numbers]

    if args.demo:
        demo(numbers)
        sys.exit()
    
    for line in sparklines(numbers, num_lines=a.num_lines, emph=a.emphasise, verbose=a.verbose):
        print(line)


if __name__ == '__main__':
    main()
