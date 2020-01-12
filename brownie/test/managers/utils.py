#!/usr/bin/python3

OUTCOMES = [
    (".", "passed"),
    ("s", "skipped"),
    ("F", "failed"),
    ("E", "error"),
    ("x", "xfailed"),
    ("X", "xpassed"),
]


def convert_outcome(value):
    return next(next(x for x in i if x != value) for i in OUTCOMES if value in i)
