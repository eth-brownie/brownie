#!/usr/bin/python3

import pytest

from brownie.cli import test


def test_apply_range():
    data = [(None, None, None, (1, 2, 3, 4, 5))]
    assert test.apply_range(data, "1:4")[0][3] == [1, 2, 3]
    assert test.apply_range(data, "3")[0][3] == [3]
    assert test.apply_range(data, "-1")[0][3] == [5]
    assert test.apply_range(data, "-3:-1")[0][3] == [3, 4]


def test_apply_range_setup():
    data = [(None, None, None, [1, 2, 'setup', 3, 4, 5])]
    assert test.apply_range(data, "1:4")[0][3] == ['setup', 1, 2, 3]
    assert test.apply_range(data, "3")[0][3] == ['setup', 3]
    assert test.apply_range(data, "-1")[0][3] == ['setup', 5]
    assert test.apply_range(data, "-3:-1")[0][3] == ['setup', 3, 4]


def test_apply_range_error():
    data = [(None, None, None, (1, 2, 'setup', 3, 4, 5))]
    with pytest.raises(SystemExit):
        test.apply_range(data, "0")
    with pytest.raises(SystemExit):
        test.apply_range(data, "-1:4")
    with pytest.raises(SystemExit):
        test.apply_range(data, "6")
