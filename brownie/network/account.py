#!/usr/bin/python3

import json
import os
import threading
from getpass import getpass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import eth_keys
from eth_hash.auto import keccak
from hexbytes import HexBytes

from brownie._config import CONFIG, _get_data_folder
from brownie._singleton import _Singleton
from brownie.convert import Wei, to_address
from brownie.exceptions import IncompatibleEVMVersion, UnknownAccount, VirtualMachineError
from brownie.network.state import _find_contract
from brownie.network.transaction import TransactionReceipt
from brownie.utils import color

from .rpc import Rpc, _revert_register
from .web3 import _resolve_address, web3

__tracebackhide__ = True
rpc = Rpc()


class Accounts(metaclass=_Singleton):

    """List-like container that holds all of the available Account instances."""

    def __init__(self) -> None:
        self._accounts: List = []
        # prevent private keys from being stored in read history
        self.add.__dict__["_private"] = True
        _revert_register(self)
        self._reset()

    def _reset(self) -> None:
        self._accounts.clear()
        try:
            self._accounts = [Account(i) for i in web3.eth.accounts]
        except Exception:
            pass

    def _revert(self, height: int) -> None:
        # must exist for rpc registry callback
        pass

    def __contains__(self, address: str) -> bool:
        try:
            address = to_address(address)
            return address in self._accounts
        except ValueError:
            return False

    def __repr__(self) -> str:
        return str(self._accounts)

    def __iter__(self) -> Iterator:
        return iter(self._accounts)

    def __getitem__(self, key: int) -> Any:
        return self._accounts[key]

    def __delitem__(self, key: int) -> None:
        del self._accounts[key]

    def __len__(self) -> int:
        return len(self._accounts)

    def add(self, priv_key: Union[int, bytes, str] = None) -> "LocalAccount":
        """Creates a new ``LocalAccount`` instance and appends it to the container.

        Args:
            priv_key: Private key of the account. If none is given, one is
                      randomly generated.

        Returns:
            Account instance."""
        private_key: Union[int, bytes, str]
        if not priv_key:
            private_key = "0x" + keccak(os.urandom(8192)).hex()
        else:
            private_key = priv_key

        w3account = web3.eth.account.from_key(private_key)
        if w3account.address in self._accounts:
            return self.at(w3account.address)
        account = LocalAccount(w3account.address, w3account, private_key)
        self._accounts.append(account)
        return account

    def load(self, filename: str = None) -> Union[List, "LocalAccount"]:
        """Loads a local account from a keystore file.

        Args:
            filename: Keystore filename. If none is given, returns a list of
                      available keystores.

        Returns:
            Account instance."""
        project_path = _get_data_folder().joinpath("accounts")
        if not filename:
            return [i.stem for i in project_path.glob("*.json")]
        filename = str(filename)
        if not filename.endswith(".json"):
            filename += ".json"
        json_file = Path(filename).expanduser()
        if not json_file.exists():
            json_file = project_path.joinpath(filename)
            if not json_file.exists():
                raise FileNotFoundError(f"Cannot find {json_file}")
        with json_file.open() as fp:
            priv_key = web3.eth.account.decrypt(
                json.load(fp), getpass("Enter the password to unlock this account: ")
            )
        return self.add(priv_key)

    def at(self, address: str) -> "LocalAccount":
        """Retrieves an Account instance from the address string. Raises
        ValueError if the account cannot be found.

        Args:
            address: string of the account address.

        Returns:
            Account instance.
        """
        address = _resolve_address(address)
        try:
            return next(i for i in self._accounts if i == address)
        except StopIteration:
            raise UnknownAccount(f"No account exists for {address}")

    def remove(self, address: str) -> None:
        """Removes an account instance from the container.

        Args:
            address: Account instance or address string of account to remove."""
        address = _resolve_address(address)
        try:
            self._accounts.remove(address)
        except ValueError:
            raise UnknownAccount(f"No account exists for {address}")

    def clear(self) -> None:
        """Empties the container."""
        self._accounts.clear()


class PublicKeyAccount:
    """Class for interacting with an Ethereum account where you do not control
    the private key. Can be used to check the balance or nonce, and to send ether to."""

    def __init__(self, addr: str) -> None:
        self.address = _resolve_address(addr)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} '{color('bright magenta')}{self.address}{color}'>"

    def __hash__(self) -> int:
        return hash(self.address)

    def __str__(self) -> str:
        return self.address

    def __eq__(self, other: Union[object, str]) -> bool:
        if isinstance(other, str):
            try:
                address = _resolve_address(other)
                return address == self.address
            except ValueError:
                return False
        if isinstance(other, PublicKeyAccount):
            return other.address == self.address
        return super().__eq__(other)

    def balance(self) -> Wei:
        """Returns the current balance at the address, in wei."""
        balance = web3.eth.getBalance(self.address)
        return Wei(balance)

    @property
    def nonce(self) -> int:
        return web3.eth.getTransactionCount(self.address)


class _PrivateKeyAccount(PublicKeyAccount):

    """Base class for Account and LocalAccount"""

    def _gas_limit(self, to: Union[str, "Accounts"], amount: Optional[int], data: str = "") -> int:
        gas_limit = CONFIG["active_network"]["gas_limit"]
        if isinstance(gas_limit, bool) or gas_limit in (None, "auto"):
            return self.estimate_gas(to, amount, data)
        return Wei(gas_limit)

    def _gas_price(self) -> Wei:
        gas_price = CONFIG["active_network"]["gas_price"]
        if isinstance(gas_price, bool) or gas_price in (None, "auto"):
            return web3.eth.gasPrice
        return Wei(gas_price)

    def _check_for_revert(self, tx: Dict) -> None:
        if not CONFIG["active_network"]["reverting_tx_gas_limit"]:
            try:
                web3.eth.call(dict((k, v) for k, v in tx.items() if v))
            except ValueError as e:
                raise VirtualMachineError(e) from None

    def deploy(
        self,
        contract: Any,
        *args: Tuple,
        amount: Optional[int] = None,
        gas_limit: Optional[int] = None,
        gas_price: Optional[int] = None,
    ) -> Any:
        """Deploys a contract.

        Args:
            contract: ContractContainer instance.
            *args: Constructor arguments. The last argument may optionally be
                   a dictionary of transaction values.

        Kwargs:
            amount: Amount of ether to send with transaction, in wei.
            gas_limit: Gas limit of the transaction.
            gas_price: Gas price of the transaction.

        Returns:
            * Contract instance if the transaction confirms
            * TransactionReceipt if the transaction is pending or reverts"""

        evm = contract._build["compiler"]["evm_version"]
        if rpc.is_active() and not rpc.evm_compatible(evm):
            raise IncompatibleEVMVersion(
                f"Local RPC using '{rpc.evm_version()}' but contract was compiled for '{evm}'"
            )
        data = contract.deploy.encode_input(*args)
        try:
            txid = self._transact(  # type: ignore
                {
                    "from": self.address,
                    "value": Wei(amount),
                    "nonce": self.nonce,
                    "gasPrice": Wei(gas_price) or self._gas_price(),
                    "gas": Wei(gas_limit) or self._gas_limit("", amount, data),
                    "data": HexBytes(data),
                }
            )
            revert_data = None
        except ValueError as e:
            txid, revert_data = _raise_or_return_tx(e)
        tx = TransactionReceipt(
            txid, self, name=contract._name + ".constructor", revert_data=revert_data
        )
        add_thread = threading.Thread(target=contract._add_from_tx, args=(tx,), daemon=True)
        add_thread.start()
        if tx.status != 1:
            return tx
        add_thread.join()
        return _find_contract(tx.contract_address)

    def estimate_gas(
        self, to: Union[str, "Accounts"], amount: Optional[int], data: str = ""
    ) -> int:
        """Estimates the gas cost for a transaction. Raises VirtualMachineError
        if the transaction would revert.

        Args:
            to: Account instance or address string of transaction recipient.
            amount: Amount of ether to send in wei.
            data: Transaction data hexstring.

        Returns:
            Estimated gas value in wei."""
        try:
            return web3.eth.estimateGas(
                {"from": self.address, "to": str(to), "value": Wei(amount), "data": HexBytes(data)}
            )
        except ValueError:
            if CONFIG["active_network"]["reverting_tx_gas_limit"]:
                return CONFIG["active_network"]["reverting_tx_gas_limit"]
            raise

    def transfer(
        self,
        to: "Accounts",
        amount: int,
        gas_limit: int = None,
        gas_price: int = None,
        data: str = "",
    ) -> "TransactionReceipt":
        """Transfers ether from this account.

        Args:
            to: Account instance or address string to transfer to.
            amount: Amount of ether to send, in wei.

        Kwargs:
            gas_limit: Gas limit of the transaction.
            gas_price: Gas price of the transaction.
            data: Hexstring of data to include in transaction.

        Returns:
            TransactionReceipt object"""

        try:
            txid = self._transact(  # type: ignore
                {
                    "from": self.address,
                    "to": str(to),
                    "value": Wei(amount),
                    "nonce": self.nonce,
                    "gasPrice": Wei(gas_price) if gas_price is not None else self._gas_price(),
                    "gas": Wei(gas_limit) or self._gas_limit(to, amount, data),
                    "data": HexBytes(data),
                }
            )
            revert_data = None
        except ValueError as e:
            txid, revert_data = _raise_or_return_tx(e)
        return TransactionReceipt(txid, self, revert_data=revert_data)


class Account(_PrivateKeyAccount):

    """Class for interacting with an Ethereum account.

    Attributes:
        address: Public address of the account.
        nonce: Current nonce of the account."""

    def _transact(self, tx: Dict) -> Any:
        self._check_for_revert(tx)
        return web3.eth.sendTransaction(tx)


class LocalAccount(_PrivateKeyAccount):

    """Class for interacting with an Ethereum account.

    Attributes:
        address: Public address of the account.
        nonce: Current nonce of the account.
        private_key: Account private key.
        public_key: Account public key."""

    def __init__(self, address: str, account: Account, priv_key: Union[int, bytes, str]) -> None:
        self._acct = account
        self.private_key = priv_key
        self.public_key = eth_keys.keys.PrivateKey(HexBytes(priv_key)).public_key
        super().__init__(address)

    def save(self, filename: str, overwrite: bool = False) -> str:
        """Encrypts the private key and saves it in a keystore json.

        Attributes:
            filename: path to keystore file. If no folder is given, saved in
                      ~/.brownie/accounts
            overwrite: if True, will overwrite an existing file.

        Returns the absolute path to the keystore file as a string.
        """
        path = _get_data_folder().joinpath("accounts")
        path.mkdir(exist_ok=True)
        filename = str(filename)
        if not filename.endswith(".json"):
            filename += ".json"
        if not any(i in r"\/" for i in filename):
            json_file = path.joinpath(filename).resolve()
        else:
            json_file = Path(filename).expanduser().resolve()
        if not overwrite and json_file.exists():
            raise FileExistsError("Account with this identifier already exists")
        encrypted = web3.eth.account.encrypt(
            self.private_key, getpass("Enter the password to encrypt this account with: ")
        )
        with json_file.open("w") as fp:
            json.dump(encrypted, fp)
        return str(json_file)

    def _transact(self, tx: Dict) -> None:
        self._check_for_revert(tx)
        signed_tx = self._acct.sign_transaction(tx).rawTransaction  # type: ignore
        return web3.eth.sendRawTransaction(signed_tx)


def _raise_or_return_tx(exc: ValueError) -> Any:
    try:
        data = eval(str(exc))["data"]
        txid = next(i for i in data.keys() if i[:2] == "0x")
        reason = data[txid]["reason"] if "reason" in data[txid] else None
        pc = data[txid]["program_counter"]
        revert_type = data[txid]["error"]
        if revert_type == "revert":
            pc -= 1
        return txid, [reason, pc, revert_type]
    except SyntaxError:
        raise exc
    except Exception:
        raise VirtualMachineError(exc) from None
