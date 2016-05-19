#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CLI Entry point for the program.
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

if sys.version_info.major >= 3:
    from sparklines.sparklines import sparklines, demo, __version__
else:
    from sparklines import sparklines, demo, __version__

try:
    import termcolor
    HAVE_TERMCOLOR = True
except ImportError:
    HAVE_TERMCOLOR = False


def _float_or_none(num_str):
    "Convert a string to a float if possible or None."

    try:
        res = float(num_str)
    except ValueError:
        res = None
    return res


def is_valid_emphasis(arg):
    if re.match('\w+\:(eq|gt|ge|lt|le)\:.+', arg):
        return arg
    else:
        return False


def main():
    desc = 'Sparklines on the command-line, '
    pi = [3, 1, 4, 5, 9, 2, 6]
    if HAVE_TERMCOLOR:
        line = sparklines(pi, emph=['red:ge:5'])[0]
    else:
        line = sparklines(pi)[0]
    desc += 'e.g. %s for %s.' % (line, pi)
    p = argparse.ArgumentParser(description=desc)

    p.add_argument('-v', '--verbose', action='store_true',
        help='Provide more verbose (debugging) output (none for now).')

    p.add_argument('-V', '--version', action='store_true',
        help='Display version number and quit.')

    p.add_argument('-d', '--demo', action='store_true',
        help='Show a few usage examples for given (mandatory) input values.')

    help_emph = 'Emphasise values below or above a certain threshold (e.g. '
    help_emph += '"green:gt:5.0"). Works only when optional dependancy ' 
    help_emph += '"termcolor" is met (which is %s here). ' % HAVE_TERMCOLOR
    help_emph += 'Otherwise has no effect.'
    p.add_argument('-e', '--emphasise', metavar='STRING',
        type=is_valid_emphasis, nargs='+',
        help=help_emph)

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
    
    for line in sparklines(numbers, num_lines=a.num_lines, emph=a.emphasise, verbose=a.verbose):
        print(line)


if __name__ == '__main__':
    main()
