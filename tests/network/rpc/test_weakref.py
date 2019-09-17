#!/usr/bin/python3

from brownie.network.rpc import _revert_refs


def test_weakref(rpc, project, testproject, accounts):
    ref_len = len(_revert_refs)
    o = project.load(testproject._project_path, "OtherProject")
    assert ref_len < len(_revert_refs)
    o.close()
    rpc.reset()
    assert ref_len < len(_revert_refs)
    del o
    rpc.reset()
    assert ref_len == len(_revert_refs)


def test_weakref_deployed(rpc, project, testproject, accounts):
    ref_len = len(_revert_refs)
    o = project.load(testproject._project_path, "OtherProject")
    o.BrownieTester.deploy(True, {"from": accounts[0]})
    del o
    rpc.reset()
    assert ref_len == len(_revert_refs)
