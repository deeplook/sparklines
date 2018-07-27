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
    from sparklines.sparklines import sparklines, demo
else:
    from sparklines import sparklines, demo


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
    desc = '''Sparklines on the command-line, e.g. ▃▁▄▁▄█▂▅ for
        3 1 4 1 5 9 2 6. Please add bug reports and suggestions to
        https://github.com/deeplook/sparklines/issues.'''
    p = argparse.ArgumentParser(description=desc)

    p.add_argument('-v', '--verbose', action='store_true',
        help='Provide more verbose (debugging) output (none for now).')

    p.add_argument('-V', '--version', action='store_true',
        help='Display version number and quit.')

    help_d = '''Show a few usage examples for given (mandatory) input
        values. All other options are ignored.'''
    p.add_argument('-d', '--demo', action='store_true',
        help=help_d)

    p.add_argument('-m', '--min', type=float,
        help='Use this value as the minimum for scaling.')

    p.add_argument('-M', '--max', type=float,
        help='Use this value as the maximum for scaling.')

    help_emph = '''Emphasise input values below or above a certain
        threshold (e.g. "green:gt:5.0"). This option takes one argument
        value, but can be given repeatedly. Works only when optional
        dependancy "termcolor" is met (which is {0!s} here). Otherwise
        has no effect.'''.format(HAVE_TERMCOLOR)
    p.add_argument('-e', '--emphasise', metavar='STRING',
        type=test_valid_emphasis, default=[], action='append',
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

    help_wrap = '''Wrap the graph to a new line after PERIOD
    data points. This is useful for data with natural periodicity:
    for example daily or weekly.
    '''
    p.add_argument('-w', '--wrap', metavar='PERIOD', type=int,
        help=help_wrap)

    a = args = p.parse_args()

    if args.version:
        print('0.4.2')  # FIXME: needs to be taken again from setup.py...
        sys.exit()

    numbers = args.nums
    if numbers == sys.stdin:
        numbers = numbers.read().strip().split()
    numbers = [_float_or_none(n) for n in numbers]

    if args.demo:
        print(demo(numbers))
        sys.exit()

    for line in sparklines(
            numbers, num_lines=a.num_lines, emph=a.emphasise,
            verbose=a.verbose, minimum=a.min, maximum=a.max,
            wrap=args.wrap):
        print(line)


if __name__ == '__main__':
    main()
