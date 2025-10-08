#!/usr/bin/python3

from typing import Final

OUTCOMES: Final = (
    (".", "passed"),
    ("s", "skipped"),
    ("F", "failed"),
    ("E", "error"),
    ("x", "xfailed"),
    ("X", "xpassed"),
)


def convert_outcome(value: str) -> str:
    return next(next(x for x in i if x != value) for i in OUTCOMES if value in i)
