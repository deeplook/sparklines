#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Text-based sparklines, e.g. on the command-line like this: ▃▁▄▁▅█▂▅.

Please read the file README.rst for more information.
"""

from __future__ import unicode_literals, print_function
import re
import sys
import warnings
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


__version__ = '0.3.0'


def _rescale(x1, y1, x2, y2, x):
    "Evaluate a straight line through two points (x1, y1) and (x2, y2) at x."

    return (y2-y1) / (x2-x1) * x + (x2*y1 - x1-y2) / (x2-x1)


def _check_negatives(numbers):
    "Raise warning for negative numbers."

    negatives = filter(lambda x: x < 0, filter(None, numbers))
    if any(negatives):
        neg_values = ', '.join(map(str, negatives))
        msg = 'Found negative value(s): %s. ' % neg_values
        msg += 'While not forbidden, the output will look unexpected.'
        warnings.warn(msg)


def _check_emphasis(numbers, emph):
    "Find index postions in list of numbers to be emphasized according to emph."

    pat = '(\w+)\:(eq|gt|ge|lt|le)\:(.+)'
    # find values to be highlighted
    emphasized = {} # index: color
    for (i, n) in enumerate(numbers):
        if n is None:
            continue
        for em in emph:
            color, op, value = re.match(pat, em).groups()
            value = float(value)
            if op == 'eq' and n == value:
                emphasized[i] = color
            elif op == 'gt' and n > value:
                emphasized[i] = color
            elif op == 'ge' and n >= value:
                emphasized[i] = color
            elif op == 'lt' and n < value:
                emphasized[i] = color
            elif op == 'le' and n <= value:
                emphasized[i] = color
    return emphasized


def sparklines(numbers=[], num_lines=1, emph=None, verbose=False):
    """
    Return a list of 'sparkline' strings for a given list of input numbers.

    The list of input numbers may contain None values, too, for which the
    resulting sparkline will contain a blank character (a space). 

    Examples:

        sparklines([3, 1, 4, 1, 5, 9, 2, 6])
        -> ['▃▁▄▁▅█▂▅']
        sparklines([3, 1, 4, 1, 5, 9, 2, 6], num_lines=2)
        -> [
            '     █ ▂',
            '▅▁▆▁██▃█'
        ]
    """

    assert num_lines > 0

    if len(numbers) == 0:
        return ['']

    # raise warning for negative numbers
    _check_negatives(numbers)

    # find min/max values, ignoring Nones
    filtered = [n for n in numbers if n is not None]
    min_ = min(filtered)
    max_ = max(filtered)
    dv = max_ - min_

    # find values to be highlighted
    emphasized = _check_emphasis(numbers, emph) if emph else {}

    blocks = " ▁▂▃▄▅▆▇█"
    if dv == 0:
        values = [4 * num_lines for x in numbers]
    elif dv > 0:
        num_blocks = len(blocks) - 1

        values = [
            (num_blocks - 1.) / dv * x + (max_*1. - min_ * num_blocks) / dv
                if not x is None else None
            for x in numbers
        ]

        if num_lines > 1:
            m = min([n for n in values if n is not None])
            values = [
                _rescale(m, m, max_, num_lines * max_, v) 
                    if not v is None else None
                for v in values
            ]
        values = [round(v) if not v is None else None for v in values]

    if num_lines > 0:
        multi_values = []
        for i in range(num_lines):
            multi_values.append([
                min(v, 8) if not v is None else None 
                for v in values
            ])
            values = [max(0, v-8) if not v is None else None for v in values]
        multi_values.reverse()
        lines = []
        for values in multi_values:
            if HAVE_TERMCOLOR and emphasized:
                tc = termcolor.colored
                res = [tc(blocks[int(v)], emphasized.get(i, 'white')) if not v is None else ' ' for (i, v) in enumerate(values)]
            else:
                res = [blocks[int(v)] if not v is None else ' ' for v in values]
            lines.append(''.join(res))
        return lines


def demo(nums=[]):
    "Print a few usage examples on stdout."

    nums = nums or [3, 1, 4, 1, 5, 9, 2, 6]

    if __name__ == '__main__':
        prog = sys.argv[0]
    else:
        prog = __file__

    print('Usage examples (command-line and programmatic use):')
    print('')

    print('Standard one-line sparkline')
    print('python %s %s' % (prog, ' '.join(map(str, nums))))
    print('>>> print(sparklines(%s)[0])' % nums)
    print(sparklines(nums)[0])
    print('')

    print('Multi-line sparkline (n=2)')
    print('python %s -n 2 %s' % (prog, ' '.join(map(str, nums))))
    print('>>> for line in sparklines(%s, num_lines=2): print(line)' % nums)
    for line in sparklines(nums, num_lines=2):
        print(line)
    print('')

    print('Multi-line sparkline (n=3)')
    print('python %s -n 3 %s' % (prog, ' '.join(map(str, nums))))
    print('>>> for line in sparklines(%s, num_lines=3): print(line)' % nums)
    for line in sparklines(nums, num_lines=3):
        print(line)
    print('')

    nums = nums + [None] + list(reversed(nums[:]))
    print('Standard one-line sparkline with gap')
    print('python %s %s' % (prog, ' '.join(map(str, nums))))
    print('>>> print(sparklines(%s)[0])' % nums)
    print(sparklines(nums)[0])
