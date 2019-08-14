#!/usr/bin/python3


def test_weakref(rpc, project, testproject, accounts):
    ref_len = len(rpc._revert_refs)
    o = project.load(testproject._project_path, 'OtherProject')
    assert ref_len < len(rpc._revert_refs)
    o.close()
    rpc.reset()
    assert ref_len < len(rpc._revert_refs)
    del o
    rpc.reset()
    assert ref_len == len(rpc._revert_refs)
