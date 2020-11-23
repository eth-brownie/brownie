import pytest

from brownie.test.managers.runner import RevertContextManager as reverts


def test_no_args(vypertester):
    with reverts():
        vypertester.revertStrings(0)


def test_revert_msg(vypertester):
    with reverts("zero"):
        vypertester.revertStrings(0)


def test_both(vypertester):
    with reverts(revert_msg="two", dev_revert_msg="dev: error"):
        vypertester.revertStrings(2)


def test_revert_msg_raises_incorrect(vypertester):
    with pytest.raises(AssertionError):
        with reverts("one"):
            vypertester.revertStrings(0)


def test_revert_msg_raises_partial(vypertester):
    with pytest.raises(AssertionError):
        with reverts("ze"):
            vypertester.revertStrings(0)


def test_revert_pattern(vypertester):
    with reverts(revert_pattern="z..o"):
        vypertester.revertStrings(0)


def test_revert_pattern_raises_incorrect(vypertester):
    with pytest.raises(AssertionError):
        with reverts(revert_pattern="foo[a-zA-Z]."):
            vypertester.revertStrings(0)


def test_revert_pattern_raises_partial(vypertester):
    with pytest.raises(AssertionError):
        with reverts(revert_pattern=".ro"):
            vypertester.revertStrings(0)


def test_dev_revert(vypertester):
    with reverts(dev_revert_msg="dev: error"):
        vypertester.revertStrings(2)


def test_dev_revert_fails(vypertester):
    with pytest.raises(AssertionError):
        with reverts(dev_revert_msg="dev: foo"):
            vypertester.revertStrings(2)


def test_dev_revert_pattern(vypertester):
    with reverts(dev_revert_pattern="[a-z]*:\\serror"):
        vypertester.revertStrings(2)


def test_dev_revert_pattern_raises_incorrect(vypertester):
    with pytest.raises(AssertionError):
        with reverts(dev_revert_pattern="bleerg[a-zA-Z]."):
            vypertester.revertStrings(2)


def test_dev_revert_pattern_raises_partial(vypertester):
    with pytest.raises(AssertionError):
        with reverts(dev_revert_pattern="\\sfoo"):
            vypertester.revertStrings(2)
