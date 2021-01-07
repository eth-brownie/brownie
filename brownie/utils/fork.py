from brownie import network
from brownie._config import CONFIG
from copy import deepcopy
import socket
import time

from contextlib import contextmanager


def find_open_port():
    """
    Use socket's built in ability to find an open port.

    https://gist.github.com/jdavis/4040223

    TODO: this isn't perfect, but it works for now
    """
    sock = socket.socket()
    sock.bind(('', 0))

    _, port = sock.getsockname()

    return port


def wait_for_port(port, host='localhost', timeout=5.0):
    """Wait until a port starts accepting TCP connections.

    https://gist.github.com/butla/2d9a4c0f35ea47b7452156c96a4e7b12

    Args:
        port (int): Port number.
        host (str): Host address on which the port should exist.
        timeout (float): In seconds. How long to wait before raising errors.
    Raises:
        TimeoutError: The port isn't accepting connection after time specified in `timeout`.
    """
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError('Waited too long for the port {} on host {} to start accepting '
                                   'connections.'.format(port, host)) from ex


@contextmanager
def fork(block=None, **cmd_settings):
    """TODO: Partly incompatible with websockets."""
    print("Forking network:", network.web3._uri, "@", block or "latest")

    # TODO: setup snapshots
    # brownie.chain.snapshot()
    old_uri = network.web3._uri

    # TODO: get the currently active network
    old_network = network.show_active()
    old_history = network.history.copy()

    network_settings = CONFIG.set_active_network(old_network)

    if block is None:
        fork = old_uri
    else:
        fork = f"{old_uri}@{block}"

    fork_port = find_open_port()

    # add our cmd_settings on top of the active network's settings
    if 'cmd_settings' in network_settings:
        network_settings['cmd_settings'].update(cmd_settings)
    else:
        network_settings['cmd_settings'] = cmd_settings

    network_settings['cmd_settings']['port'] = fork_port
    network_settings['cmd_settings']['fork'] = fork

    timeout = network_settings.get("timeout", 30)

    # TODO: allow overriding this?
    cmd = "ganache-cli"

    forked_rpc = None

    try:
        # launch a new rpc that forks the currently active rpc
        forked_rpc = network.rpc.launch(cmd, extra=True, **network_settings['cmd_settings'])

        # wait for ganache to start
        wait_for_port(fork_port)

        # disconnect from the parent rpc
        network.web3.disconnect()

        # connect to our forked rpc
        network.web3.connect(f"http://localhost:{fork_port}", timeout)

        print("Now using network:", network.web3._uri, "@", network.chain.height)

        yield network_settings
    finally:
        # disconnect from the forked rpc
        network.web3.disconnect()

        if forked_rpc:
            # kill this rpc and put the previous back
            network.rpc.kill_more(forked_rpc, False)

        # connect to the previous rpc. this might be another fork
        network.web3.connect(old_uri, timeout)

        # TODO: put the global state back
        # ? CONFIG.set_active_network(old_network) ?
        network.history._list = old_history
        network.accounts._reset()
        # TODO: reset more?

        print("Returned to network:", network.web3._uri, "@", network.chain.height)