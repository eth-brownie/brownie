#!/usr/bin/python3

from unittest.mock import MagicMock, patch

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


def test_no_docker(rpc):
    with patch("brownie.network.rpc._get_pid_from_connections", MagicMock(value=1337)):
        with patch(
            "brownie.network.rpc._get_pid_from_net_connections"
        ) as _get_pid_from_net_connections_call:
            rpc._find_rpc_process_pid(("laddr-tuple"))
            _get_pid_from_net_connections_call.assert_not_called()


def test_dockerized_rpc_osx(rpc):
    with patch(
        "brownie.network.rpc._get_pid_from_connections", MagicMock(side_effect=ProcessLookupError)
    ):
        with patch("platform.system", MagicMock(return_value="Darwin")):
            with patch("brownie.network.rpc._find_proc_by_name") as find_proc_by_name_call:
                rpc._find_rpc_process_pid(("laddr-tuple"))
                find_proc_by_name_call.assert_called_with("com.docker.backend")


def test_dockerized_rpc(rpc):
    with patch(
        "brownie.network.rpc._get_pid_from_connections", MagicMock(side_effect=ProcessLookupError)
    ):
        with patch("platform.system", MagicMock(return_value="Not Darwin")):
            with patch("brownie.network.rpc._check_net_connections") as check_net_connections_call:
                rpc._find_rpc_process_pid(("laddr-tuple"))
                check_net_connections_call.assert_called()
