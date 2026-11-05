from types import SimpleNamespace

import pytest

from brownie.network.rpc import Rpc


@pytest.mark.parametrize("snapshot_id", [1, "0x1"])
def test_native_snapshot_preserves_backend_identifier(chain, monkeypatch, snapshot_id):
    monkeypatch.setattr(Rpc(), "backend", SimpleNamespace(snapshot=lambda: snapshot_id))
    previous = chain._snapshot_time_offsets.copy()
    try:
        assert chain._take_snapshot() == snapshot_id
        assert chain._snapshot_time_offsets[snapshot_id] == chain._time_offset
    finally:
        chain._snapshot_time_offsets.clear()
        chain._snapshot_time_offsets.update(previous)
