import json
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock, get_ident
from types import FunctionType, TracebackType
from typing import Any, Dict, List, Optional, Tuple, Union
from warnings import warn

from lazy_object_proxy import Proxy
from wrapt import ObjectProxy

from brownie._config import BROWNIE_FOLDER, CONFIG
from brownie.network import accounts, web3
from brownie.network.contract import Contract, ContractCall
from brownie.project import compile_source

DATA_DIR = BROWNIE_FOLDER.joinpath("data")
MULTICALL3_ABI = json.loads(DATA_DIR.joinpath("interfaces", "Multicall3.json").read_text())
MULTICALL3_SOURCE = DATA_DIR.joinpath("contracts", "Multicall3.sol").read_text()
MULTICALL3_BYTECODE = "0x6080604052600436106100f35760003560e01c80634d2301cc1161008a578063a8b0574e11610059578063a8b0574e1461025a578063bce38bd714610275578063c3077fa914610288578063ee82ac5e1461029b57600080fd5b80634d2301cc146101ec57806372425d9d1461022157806382ad56cb1461023457806386d516e81461024757600080fd5b80633408e470116100c65780633408e47014610191578063399542e9146101a45780633e64a696146101c657806342cbb15c146101d957600080fd5b80630f28c97d146100f8578063174dea711461011a578063252dba421461013a57806327e86d6e1461015b575b600080fd5b34801561010457600080fd5b50425b6040519081526020015b60405180910390f35b61012d610128366004610a85565b6102ba565b6040516101119190610bbe565b61014d610148366004610a85565b6104ef565b604051610111929190610bd8565b34801561016757600080fd5b50437fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0140610107565b34801561019d57600080fd5b5046610107565b6101b76101b2366004610c60565b610690565b60405161011193929190610cba565b3480156101d257600080fd5b5048610107565b3480156101e557600080fd5b5043610107565b3480156101f857600080fd5b50610107610207366004610ce2565b73ffffffffffffffffffffffffffffffffffffffff163190565b34801561022d57600080fd5b5044610107565b61012d610242366004610a85565b6106ab565b34801561025357600080fd5b5045610107565b34801561026657600080fd5b50604051418152602001610111565b61012d610283366004610c60565b61085a565b6101b7610296366004610a85565b610a1a565b3480156102a757600080fd5b506101076102b6366004610d18565b4090565b60606000828067ffffffffffffffff8111156102d8576102d8610d31565b60405190808252806020026020018201604052801561031e57816020015b6040805180820190915260008152606060208201528152602001906001900390816102f65790505b5092503660005b8281101561047757600085828151811061034157610341610d60565b6020026020010151905087878381811061035d5761035d610d60565b905060200281019061036f9190610d8f565b6040810135958601959093506103886020850185610ce2565b73ffffffffffffffffffffffffffffffffffffffff16816103ac6060870187610dcd565b6040516103ba929190610e32565b60006040518083038185875af1925050503d80600081146103f7576040519150601f19603f3d011682016040523d82523d6000602084013e6103fc565b606091505b50602080850191909152901515808452908501351761046d577f08c379a000000000000000000000000000000000000000000000000000000000600052602060045260176024527f4d756c746963616c6c333a2063616c6c206661696c656400000000000000000060445260846000fd5b5050600101610325565b508234146104e6576040517f08c379a000000000000000000000000000000000000000000000000000000000815260206004820152601a60248201527f4d756c746963616c6c333a2076616c7565206d69736d6174636800000000000060448201526064015b60405180910390fd5b50505092915050565b436060828067ffffffffffffffff81111561050c5761050c610d31565b60405190808252806020026020018201604052801561053f57816020015b606081526020019060019003908161052a5790505b5091503660005b8281101561068657600087878381811061056257610562610d60565b90506020028101906105749190610e42565b92506105836020840184610ce2565b73ffffffffffffffffffffffffffffffffffffffff166105a66020850185610dcd565b6040516105b4929190610e32565b6000604051808303816000865af19150503d80600081146105f1576040519150601f19603f3d011682016040523d82523d6000602084013e6105f6565b606091505b5086848151811061060957610609610d60565b602090810291909101015290508061067d576040517f08c379a000000000000000000000000000000000000000000000000000000000815260206004820152601760248201527f4d756c746963616c6c333a2063616c6c206661696c656400000000000000000060448201526064016104dd565b50600101610546565b5050509250929050565b43804060606106a086868661085a565b905093509350939050565b6060818067ffffffffffffffff8111156106c7576106c7610d31565b60405190808252806020026020018201604052801561070d57816020015b6040805180820190915260008152606060208201528152602001906001900390816106e55790505b5091503660005b828110156104e657600084828151811061073057610730610d60565b6020026020010151905086868381811061074c5761074c610d60565b905060200281019061075e9190610e76565b925061076d6020840184610ce2565b73ffffffffffffffffffffffffffffffffffffffff166107906040850185610dcd565b60405161079e929190610e32565b6000604051808303816000865af19150503d80600081146107db576040519150601f19603f3d011682016040523d82523d6000602084013e6107e0565b606091505b506020808401919091529015158083529084013517610851577f08c379a000000000000000000000000000000000000000000000000000000000600052602060045260176024527f4d756c746963616c6c333a2063616c6c206661696c656400000000000000000060445260646000fd5b50600101610714565b6060818067ffffffffffffffff81111561087657610876610d31565b6040519080825280602002602001820160405280156108bc57816020015b6040805180820190915260008152606060208201528152602001906001900390816108945790505b5091503660005b82811015610a105760008482815181106108df576108df610d60565b602002602001015190508686838181106108fb576108fb610d60565b905060200281019061090d9190610e42565b925061091c6020840184610ce2565b73ffffffffffffffffffffffffffffffffffffffff1661093f6020850185610dcd565b60405161094d929190610e32565b6000604051808303816000865af19150503d806000811461098a576040519150601f19603f3d011682016040523d82523d6000602084013e61098f565b606091505b506020830152151581528715610a07578051610a07576040517f08c379a000000000000000000000000000000000000000000000000000000000815260206004820152601760248201527f4d756c746963616c6c333a2063616c6c206661696c656400000000000000000060448201526064016104dd565b506001016108c3565b5050509392505050565b6000806060610a2b60018686610690565b919790965090945092505050565b60008083601f840112610a4b57600080fd5b50813567ffffffffffffffff811115610a6357600080fd5b6020830191508360208260051b8501011115610a7e57600080fd5b9250929050565b60008060208385031215610a9857600080fd5b823567ffffffffffffffff811115610aaf57600080fd5b610abb85828601610a39565b90969095509350505050565b6000815180845260005b81811015610aed57602081850181015186830182015201610ad1565b81811115610aff576000602083870101525b50601f017fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0169290920160200192915050565b600082825180855260208086019550808260051b84010181860160005b84811015610bb1578583037fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe001895281518051151584528401516040858501819052610b9d81860183610ac7565b9a86019a9450505090830190600101610b4f565b5090979650505050505050565b602081526000610bd16020830184610b32565b9392505050565b600060408201848352602060408185015281855180845260608601915060608160051b870101935082870160005b82811015610c52577fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa0888703018452610c40868351610ac7565b95509284019290840190600101610c06565b509398975050505050505050565b600080600060408486031215610c7557600080fd5b83358015158114610c8557600080fd5b9250602084013567ffffffffffffffff811115610ca157600080fd5b610cad86828701610a39565b9497909650939450505050565b838152826020820152606060408201526000610cd96060830184610b32565b95945050505050565b600060208284031215610cf457600080fd5b813573ffffffffffffffffffffffffffffffffffffffff81168114610bd157600080fd5b600060208284031215610d2a57600080fd5b5035919050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052604160045260246000fd5b7f4e487b7100000000000000000000000000000000000000000000000000000000600052603260045260246000fd5b600082357fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff81833603018112610dc357600080fd5b9190910192915050565b60008083357fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe1843603018112610e0257600080fd5b83018035915067ffffffffffffffff821115610e1d57600080fd5b602001915036819003821315610a7e57600080fd5b8183823760009101908152919050565b600082357fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc1833603018112610dc357600080fd5b600082357fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa1833603018112610dc357600080fdfea2646970667358221220bb2b5c71a328032f97c676ae39a1ec2148d3e5d6f73d95e9b17910152d61f16264736f6c634300080c0033"


@dataclass
class Call:

    calldata: Tuple[str, bytes]
    decoder: FunctionType


class Result(ObjectProxy):
    """A proxy object to be updated with the result of a multicall."""

    def __repr__(self) -> str:
        return repr(self.__wrapped__)


class LazyResult(Proxy):
    """A proxy object to be updated with the result of a multicall."""

    def __repr__(self) -> str:
        return repr(self.__wrapped__)


class Multicall:
    """Context manager for batching multiple calls to constant contract functions."""

    _lock = Lock()

    def __init__(self) -> None:
        self.address = None
        self._block_number = defaultdict(lambda: None)  # type: ignore
        self._contract = None
        self._pending_calls: Dict[int, List[Call]] = defaultdict(list)
        self.state_override = None

        setattr(ContractCall, "__original_call_code", ContractCall.__call__.__code__)
        setattr(ContractCall, "__proxy_call_code", self._proxy_call.__code__)
        setattr(ContractCall, "__multicall", defaultdict(lambda: None))
        ContractCall.__call__.__code__ = self._proxy_call.__code__

    @property
    def block_number(self) -> int:
        return self._block_number[get_ident()]

    def __call__(
        self, address: Optional[str] = None, block_identifier: Union[str, bytes, int, None] = None
    ) -> "Multicall":
        self.address = address  # type: ignore
        self._block_number[get_ident()] = block_identifier  # type: ignore
        return self

    def _flush(self, future_result: Result = None) -> Any:
        pending_calls = self._pending_calls[get_ident()]
        self._pending_calls[get_ident()] = []

        if not pending_calls:
            # either all calls have already been made
            # or this result has already been retrieved
            return future_result

        with self._lock:
            block_identifier = self._block_number[get_ident()]

            # we encode_input and do a web3.eth.call here instead of using __call__ because that catches errors that we need to intercept here
            target_data = self._contract.tryAggregate.encode_input(
                False,
                [_call.calldata for _call in pending_calls],
            )

            data = {"to": self._contract.address, "data": target_data}

            if self.state_override is NotImplemented:
                results = None
            elif self.state_override:
                try:
                    results = web3.eth.call(data, block_identifier, self.state_override)
                except ValueError as e:
                    # TODO: this is annoying. every site seems to do it different
                    if (
                        str(e)
                        == "{'code': -32602, 'message': 'Expected between 1 and 2 arguments and got 3'}"
                    ):
                        # eth_call did not expect the third "state_override" option. not all clients do so this is not unexpected
                        results = None
                    else:
                        raise
            else:
                results = web3.eth.call(data, block_identifier)

            if results is None:
                warn(
                    f"Multicall does not exist at block {block_identifier} and client does not support call state overrides"
                )
                for _call in pending_calls:
                    target, targetData = _call.calldata

                    data = {"to": target, "data": targetData}

                    try:
                        result = web3.eth.call(data, block_identifier)
                    except Exception as e:
                        # TODO: what exceptions should we catch?
                        result = None

                    _call.__wrapped__ = _call.decoder(result) if result is not None else None

                return future_result

        results = self._contract.tryAggregate.decode_output(results)

        for _call, result in zip(pending_calls, results):
            # TODO: check result[0] is not None?
            _call.__wrapped__ = _call.decoder(result[1]) if result[0] else None  # type: ignore

        return future_result

    def flush(self) -> Any:
        """Flush the pending queue of calls, retrieving all the results."""
        return self._flush()

    def _call_contract(self, call: ContractCall, *args: Tuple, **kwargs: Dict[str, Any]) -> Proxy:
        """Add a call to the buffer of calls to be made"""
        calldata = (call._address, call.encode_input(*args, **kwargs))  # type: ignore
        call_obj = Call(calldata, call.decode_output)  # type: ignore
        # future result
        result = Result(call_obj)
        self._pending_calls[get_ident()].append(result)

        return LazyResult(lambda: self._flush(result))

    @staticmethod
    def _proxy_call(*args: Tuple, **kwargs: Dict[str, Any]) -> Any:
        """Proxy code which substitutes `ContractCall.__call__"""
        self = getattr(ContractCall, "__multicall", {}).get(get_ident())
        if self:
            return self._call_contract(*args, **kwargs)

        # standard call we let pass through
        ContractCall.__call__.__code__ = getattr(ContractCall, "__original_call_code")
        result = ContractCall.__call__(*args, **kwargs)  # type: ignore
        ContractCall.__call__.__code__ = getattr(ContractCall, "__proxy_call_code")
        return result

    def __enter__(self) -> "Multicall":
        """Enter the Context Manager and substitute `ContractCall.__call__`"""
        # we set the code objects on ContractCall class so we can grab them later

        active_network = CONFIG.active_network

        # TODO: check multicall2 and multicall3
        # that way, if we don't have a client that supports state overrides, we can still query older blocks
        if "multicall3" in active_network:
            self.address = active_network["multicall3"]

        self._block_number[get_ident()] = (
            self._block_number[get_ident()] or web3.eth.get_block_number()
        )

        if self.address is None:
            # default to the [multicall3 address](https://github.com/mds1/multicall/)
            self.address = "0xcA11bde05977b3631167028862bE2a173976CA11"

        if not web3.eth.get_code(self.address, block_identifier=self.block_number):
            # the multicall contract isn't deployed. use state overrides
            if "ganache" in CONFIG.active_network.get("cmd", ""):
                # depends on https://github.com/trufflesuite/ganache/pull/2565 (slated for ganache v7.1.0)
                self.state_override = NotImplemented
            else:
                self.state_override = {
                    self.address: {
                        "code": MULTICALL3_BYTECODE,
                    },
                }

        self._contract = Contract.from_abi("Multicall", self.address, MULTICALL3_ABI)
        getattr(ContractCall, "__multicall")[get_ident()] = self

    def __exit__(self, exc_type: Exception, exc_val: Any, exc_tb: TracebackType) -> None:
        """Exit the Context Manager and reattach original `ContractCall.__call__` code"""
        self.flush()
        getattr(ContractCall, "__multicall")[get_ident()] = None

    @staticmethod
    def deploy(tx_params: Dict) -> Contract:
        """Deploy an instance of the `Multicall3` contract.

        Args:
            tx_params: parameters passed to the `deploy` method of the `Multicall3` contract
                container.
        """
        # TODO: deploy with singleton deployer
        project = compile_source(MULTICALL3_SOURCE)
        deployment = project.Multicall3.deploy(tx_params)  # type: ignore
        CONFIG.active_network["multicall3"] = deployment.address
        return deployment
