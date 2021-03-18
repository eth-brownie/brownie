#!/usr/bin/python3

import pytest


@pytest.fixture
def attachable_rpc(temp_rpc):
    r = temp_rpc.process
    temp_rpc.process = None
    yield temp_rpc
    temp_rpc.process = r


def test_attach_lookup_error(no_rpc):
    with pytest.raises(ProcessLookupError):
        no_rpc.attach("http://127.0.0.1:7545")


def test_already_active(temp_rpc, temp_port):
    with pytest.raises(SystemError):
        temp_rpc.attach(f"http://127.0.0.1:{temp_port}")


def test_attach(attachable_rpc, temp_port):
    attachable_rpc.attach(f"http://127.0.0.1:{temp_port}")
    attachable_rpc.process = None
    attachable_rpc.attach(("127.0.0.1", temp_port))
    assert attachable_rpc.is_active()


def test_kill(attachable_rpc, temp_port):
    attachable_rpc.attach(f"http://127.0.0.1:{temp_port}")
    attachable_rpc.kill()
    with pytest.raises(SystemError):
        attachable_rpc.kill()
    attachable_rpc.kill(False)


def test_no_port(rpc):
    with pytest.raises(ValueError):
        rpc.attach("http://127.0.0.1")
