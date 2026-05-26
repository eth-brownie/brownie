#!/usr/bin/python3

import json
from contextlib import suppress
from typing import Any

import pytest

import brownie.network.contract as contract_module


class MockExplorerResponse:
    status_code = 200

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self.text = json.dumps(data)

    def json(self) -> dict[str, Any]:
        return self._data


class MockExplorer:
    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._responses: dict[str, dict[str, dict[str, Any]]] = {}
        self._code: dict[str, str] = {}
        self.calls: list[dict[str, Any]] = []
        self._original_get_code = contract_module.web3.eth.get_code
        self._original_get_storage_at = contract_module.web3.eth.get_storage_at

        monkeypatch.setattr(contract_module.requests, "get", self._get)
        monkeypatch.setattr(contract_module.web3.eth, "get_code", self._get_code)
        monkeypatch.setattr(contract_module.web3.eth, "get_storage_at", self._get_storage_at)

    def add_source(
        self,
        address: str,
        *,
        name: str,
        abi: list[dict[str, Any]],
        source: str,
        compiler_version: str,
        optimization_used: str = "1",
        runs: str = "200",
        evm_version: str = "Default",
        implementation: str = "",
        bytecode: str = "0x6000",
    ) -> str:
        address = self._normalize(address)
        self.set_code(address, bytecode)
        self._responses.setdefault(address, {})["getsourcecode"] = {
            "status": "1",
            "result": [
                {
                    "SourceCode": source,
                    "ABI": json.dumps(abi),
                    "ContractName": name,
                    "CompilerVersion": compiler_version,
                    "OptimizationUsed": optimization_used,
                    "Runs": runs,
                    "EVMVersion": evm_version,
                    "Implementation": implementation,
                }
            ],
        }
        return address

    def add_abi_only(
        self,
        address: str,
        *,
        abi: list[dict[str, Any]],
        bytecode: str = "0x6000",
    ) -> str:
        address = self._normalize(address)
        self.set_code(address, bytecode)
        self._responses.setdefault(address, {}).update(
            {
                "getsourcecode": {
                    "status": "1",
                    "result": [{"SourceCode": "", "ABI": "Contract source code not verified"}],
                },
                "getabi": {"status": "1", "result": json.dumps(abi)},
            }
        )
        return address

    def add_unverified(self, address: str, *, bytecode: str = "0x6000") -> str:
        address = self._normalize(address)
        self.set_code(address, bytecode)
        self._responses.setdefault(address, {}).update(
            {
                "getsourcecode": {
                    "status": "1",
                    "result": [{"SourceCode": "", "ABI": "Contract source code not verified"}],
                },
                "getabi": {"status": "0", "result": "Contract source code not verified"},
            }
        )
        return address

    def set_code(self, address: str, bytecode: str = "0x6000") -> str:
        address = self._normalize(address)
        self._code[address] = bytecode if bytecode.startswith("0x") else f"0x{bytecode}"
        return address

    def actions(self, address: str | None = None) -> list[str]:
        if address is None:
            return [call["action"] for call in self.calls]

        address = self._normalize(address)
        return [call["action"] for call in self.calls if call["address"] == address]

    def cleanup(self) -> None:
        for address in set(self._responses) | set(self._code):
            contract_module._unverified_addresses.discard(address)
            with suppress(Exception):
                contract_module.Contract.remove_deployment(address)

    def _get(self, _url: str, params: dict[str, Any], **_kwargs: Any) -> MockExplorerResponse:
        address = self._normalize(params["address"])
        action = params["action"]
        self.calls.append({"address": address, "action": action, "params": params.copy()})

        try:
            data = self._responses[address][action]
        except KeyError:
            raise AssertionError(f"No mock explorer response for {address} {action}") from None

        return MockExplorerResponse(data)

    def _get_code(self, address: str, *args: Any, **kwargs: Any) -> Any:
        try:
            address = self._normalize(address)
        except ValueError:
            return self._original_get_code(address, *args, **kwargs)

        if address in self._code:
            return contract_module.HexBytes(self._code[address])
        return self._original_get_code(address, *args, **kwargs)

    def _get_storage_at(self, address: str, *args: Any, **kwargs: Any) -> Any:
        try:
            address = self._normalize(address)
        except ValueError:
            return self._original_get_storage_at(address, *args, **kwargs)

        if address in self._code:
            return contract_module.HexBytes("0x" + "00" * 32)
        return self._original_get_storage_at(address, *args, **kwargs)

    @staticmethod
    def _normalize(address: str) -> str:
        return contract_module._resolve_address(address)


@pytest.fixture
def mock_explorer(devnetwork, config, monkeypatch):
    config.active_network["chainid"] = 1
    config.active_network["explorer"] = "https://api.etherscan.io/api"
    monkeypatch.setenv("ETHERSCAN_TOKEN", "mock-token")

    explorer = MockExplorer(monkeypatch)
    yield explorer
    explorer.cleanup()
