#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CLI Entry point for the program.
"""

from __future__ import unicode_literals, print_function
import sys
import argparse

# handle different file types in Python 2 and 3
try:
    import io
    file = io.IOBase
except ImportError:
    pass

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


def main():
    desc = 'Sparklines on the command-line, '
    desc += 'e.g. ▃▁▄▁▅█▂▅ for [3, 1, 4, 5, 9, 2, 6].'
    p = argparse.ArgumentParser(description=desc)

    p.add_argument('-v', '--verbose', action='store_true',
        help='Provide more verbose (debugging) output (none for now).')

    p.add_argument('-V', '--version', action='store_true',
        help='Display version number and quit.')

    p.add_argument('-d', '--demo', action='store_true',
        help='Show a few usage examples for given (mandatory) input values.')

    help_n = 'The number of lines for one sparkline (higher numbers increase '
    help_n += 'the resolution). An integer >= 1 (default: 1).'
    p.add_argument('-n', '--num-lines', metavar='NUMBER',
        help=help_n, default='1', type=int)

    help_nums = 'A positive numeric value >= 0, e.g. 0, 3.14, 2e2 or '
    help_nums += 'null/None... Negative numbers work, too, but will give '
    help_nums += 'unexpected results and raise a warning.'
    p.add_argument('nums', metavar='VALUE',
        help=help_nums, nargs='*', default=sys.stdin)

    a = args = p.parse_args()

    if args.version:
        print(__version__)
        sys.exit()

    numbers = args.nums
    if type(numbers) == file:
        numbers = numbers.read().split()
    numbers = [_float_or_none(n) for n in numbers]

    if args.demo:
        demo(numbers)
        sys.exit()
    
    for line in sparklines(numbers, num_lines=a.num_lines, verbose=a.verbose):
        print(line)


if __name__ == '__main__':
    main()
