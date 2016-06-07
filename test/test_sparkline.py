#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run from the root folder with either 'python setup.py test' or 
'py.test test/test_sparkline.py'.
"""

from __future__ import unicode_literals, print_function

from sparklines import sparklines, scale_values


def test_scale0():
    "Test scale..."

    res = scale_values([1, 2, 3])
    exp = [1., 4., 8.]
    assert res == exp


def test_scale1():
    "Test scale..."

    res = scale_values([1, 2, 3], num_lines=2)
    exp = [1., 9., 18.]
    assert res == exp


def test_scale_pi():
    "Test scale Pi."

    res = scale_values([3, 1, 4, 1, 5, 9, 2, 6])
    exp = [3, 1, 4, 1, 4, 8, 2, 5]
    assert res == exp


def test_pi():
    "Test first eight digits of Pi."

    res = sparklines([3, 1, 4, 1, 5, 9, 2, 6])
    exp = ['▃▁▄▁▄█▂▅']
    assert res == exp


def test_minmax():
    "Test two values, min and max."

    res = sparklines([1, 8])
    exp = ['▁█'] # 1, 8
    assert res == exp


def test_rounding0():
    "Test two values, min and max."

    res = sparklines([1, 5, 8])
    exp = ['▁▅█'] # 1, 5, 8
    assert res == exp


def test1():
    "Test single values all have the same four pixel high output character."

    for i in range(10):
        res = sparklines([3])
        exp = ['▄']
        assert res == exp
