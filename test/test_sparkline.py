#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run from the root folder with either 'python setup.py test' or 
'py.test test/test_sparkline.py'.
"""

from __future__ import unicode_literals, print_function

from sparkline import sparklines


def test0():
    "Test first eight digits of Pi."

    res = sparklines([3, 1, 4, 1, 5, 9, 2, 6])
    exp = ['▃▁▄▁▅█▂▅']
    assert res == exp


def test1():
    "Test single values all have the same four pixel high output character."

    for i in range(10):
        res = sparklines([3])
        exp = ['▄']
        assert res == exp
