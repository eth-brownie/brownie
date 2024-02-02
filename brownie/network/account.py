#!/usr/bin/python3

import json
import sys
import threading
import time
from collections import deque
from collections.abc import Iterator
from getpass import getpass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import eth_account
import eth_keys
import rlp
from eip712.messages import EIP712Message
from eth_account._utils.signing import sign_message_hash
from eth_account.datastructures import SignedMessage
from eth_account.messages import _hash_eip191_message, defunct_hash_message
from eth_utils import keccak
from eth_utils.applicators import apply_formatters_to_dict
from hexbytes import HexBytes
from web3 import HTTPProvider, IPCProvider
from web3.exceptions import InvalidTransaction, TransactionNotFound

from brownie._config import CONFIG, _get_data_folder
from brownie._singleton import _Singleton
from brownie.convert import EthAddress, Wei, to_address
from brownie.exceptions import (
    ContractNotFound,
    TransactionError,
    UnknownAccount,
    VirtualMachineError,
)
from brownie.utils import color

from .gas.bases import GasABC
from .rpc import Rpc
from .state import Chain, TxHistory, _revert_register
from .transaction import TransactionReceipt
from .web3 import _resolve_address, web3

history = TxHistory()
rpc = Rpc()

eth_account.Account.enable_unaudited_hdwallet_features()
_marker = deque("-/|\\-/|\\")


class Accounts(metaclass=_Singleton):
    """
    List-like container that holds all available `Account` objects.

    Attributes
    ----------
    default : Account, optional
        Default account to broadcast transactions from.
    """

    def __init__(self) -> None:
        self.default = None
        self._accounts: List = []

        # prevent sensitive info from being stored in readline history
        self.add.__dict__["_private"] = True
        self.from_mnemonic.__dict__["_private"] = True

        _revert_register(self)
        self._reset()

    def _reset(self) -> None:
        self._accounts.clear()
        try:
            self._accounts = [Account(i) for i in web3.eth.accounts]
        except Exception:
            pass

        # Check if accounts were manually unlocked and add them
        try:
            unlocked_accounts = CONFIG.active_network["cmd_settings"]["unlock"]
            if not isinstance(unlocked_accounts, list):
                unlocked_accounts = [unlocked_accounts]
            for address in unlocked_accounts:
                if isinstance(address, int):
                    address = HexBytes(address.to_bytes(20, "big")).hex()
                account = Account(address)
                if account not in self._accounts:
                    self._accounts.append(account)
        except (ConnectionError, ValueError, KeyError):
            pass

        if self.default not in self._accounts:
            self.default = None

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
        if CONFIG.argv["cli"] == "console":
            return str(self._accounts)
        return super().__repr__()

    def __iter__(self) -> Iterator:
        return iter(self._accounts)

    def __getitem__(self, key: int) -> "_PrivateKeyAccount":
        return self._accounts[key]

    def __delitem__(self, key: int) -> None:
        del self._accounts[key]

    def __len__(self) -> int:
        return len(self._accounts)

    def add(self, private_key: Union[int, bytes, str] = None) -> "LocalAccount":
        """
        Create a new ``LocalAccount`` instance and appends it to the container.

        When the no private key is given, a mnemonic is also generated and outputted.

        Arguments
        ---------
        private_key : int | bytes | str, optional
            Private key of the account. If none is given, one is randomly generated.

        Returns
        -------
        LocalAccount
        """
        if private_key is None:
            w3account, mnemonic = eth_account.Account.create_with_mnemonic()
            print(f"mnemonic: '{color('bright cyan')}{mnemonic}{color}'")
        else:
            w3account = web3.eth.account.from_key(private_key)

        if w3account.address in self._accounts:
            return self.at(w3account.address)

        account = LocalAccount(w3account.address, w3account, w3account.key)
        self._accounts.append(account)

        return account

    def from_mnemonic(
        self, mnemonic: str, count: int = 1, offset: int = 0, passphrase: str = ""
    ) -> Union["LocalAccount", List["LocalAccount"]]:
        """
        Generate one or more `LocalAccount` objects from a seed phrase.

        Arguments
        ---------
        mnemonic : str
            Space-separated list of BIP39 mnemonic seed words
        count : int, optional
            The number of `LocalAccount` objects to create
        offset : int, optional
            The initial account index to create accounts from
        passphrase : str, optional
            Additional passphrase to combine with the mnemonnic
        """
        new_accounts = []

        for i in range(offset, offset + count):
            w3account = eth_account.Account.from_mnemonic(
                mnemonic, passphrase=passphrase, account_path=f"m/44'/60'/0'/0/{i}"
            )

            account = LocalAccount(w3account.address, w3account, w3account.key)
            new_accounts.append(account)
            if account not in self._accounts:
                self._accounts.append(account)

        if count == 1:
            return new_accounts[0]
        return new_accounts

    def load(
        self, filename: str = None, password: str = None, allow_retry: bool = False
    ) -> Union[List, "LocalAccount"]:
        """
        Load a local account from a keystore file.

        Arguments
        ---------
        filename: str
            Keystore filename. If `None`, returns a list of available keystores.
        password: str
            Password to unlock the keystore. If `None`, password is entered via
            a getpass prompt.
        allow_retry: bool
            If True, allows re-attempt when the given password is incorrect.

        Returns
        -------
        LocalAccount
        """
        base_accounts_path = _get_data_folder().joinpath("accounts")
        if not filename:
            return [i.stem for i in base_accounts_path.glob("*.json")]

        filename = str(filename)
        json_file = Path(filename).expanduser()

        if not json_file.exists() or json_file.is_dir():
            temp_json_file = json_file.with_suffix(".json")
            if temp_json_file.exists():
                json_file = temp_json_file
            else:
                json_file_name = json_file.name
                json_file = base_accounts_path.joinpath(json_file_name)
                if json_file.suffix != ".json":
                    json_file = json_file.with_suffix(".json")
                if not json_file.exists():
                    raise FileNotFoundError(f"Cannot find {json_file}")

        with json_file.open() as fp:
            encrypted = json.load(fp)

        prompt = f'Enter password for "{json_file.stem}": '
        while True:
            if password is None:
                password = getpass(prompt)
            try:
                priv_key = web3.eth.account.decrypt(encrypted, password)
                break
            except ValueError as e:
                if allow_retry:
                    prompt = "Incorrect password, try again: "
                    password = None
                    continue
                raise e

        return self.add(priv_key)

    def at(self, address: str, force: bool = False) -> "LocalAccount":
        """
        Retrieve an `Account` instance from the address string.

        Raises `ValueError` if the account cannot be found.

        Arguments
        ---------
        address: string
            Address of the account
        force: bool
            When True, will add the account even if it was not found in web3.eth.accounts

        Returns
        -------
        Account
        """
        address = _resolve_address(address)
        acct = next((i for i in self._accounts if i == address), None)

        if acct is None and (address in web3.eth.accounts or force):
            acct = Account(address)

            if CONFIG.network_type == "development" and address not in web3.eth.accounts:
                rpc.unlock_account(address)

            self._accounts.append(acct)

        if acct:
            return acct
        raise UnknownAccount(f"No account exists for {address}")

    def remove(self, address: Union[str, "Account"]) -> None:
        """
        Remove an `Account` instance from the container.

        Arguments
        ---------
        address: str | Account
            Account instance, or string of the account address.
        """
        address = _resolve_address(str(address))
        try:
            self._accounts.remove(address)
        except ValueError:
            raise UnknownAccount(f"No account exists for {address}")

    def clear(self) -> None:
        """
        Empty the container.
        """
        self._accounts.clear()

    def connect_to_clef(self, uri: str = None, timeout: int = 120) -> None:
        """
        Connect to Clef and import open accounts.

        Clef is an account signing utility packaged with Geth, which can be
        used to interact with HW wallets in Brownie. Before calling this
        function, Clef must be running in another command prompt.

        Arguments
        ---------
        uri : str
            IPC path or http url to use to connect to clef. If None is given,
            uses the default IPC path on Unix systems or localhost on Windows.
        timeout : int
            The number of seconds to wait on a clef request before raising a
            timeout exception.
        """
        provider = None
        if uri is None:
            if sys.platform == "win32":
                uri = "http://localhost:8550/"
            else:
                uri = Path.home().joinpath(".clef/clef.ipc").as_posix()
        try:
            if Path(uri).exists():
                provider = IPCProvider(uri, timeout=timeout)
        except OSError:
            if uri is not None and uri.startswith("http"):
                provider = HTTPProvider(uri, {"timeout": timeout})
        if provider is None:
            raise ValueError("Unknown URI, must be IPC socket path or URL starting with 'http'")

        response = provider.make_request("account_list", [])
        if "error" in response:
            raise ValueError(response["error"]["message"])

        for address in response["result"]:
            if to_address(address) not in self._accounts:
                self._accounts.append(ClefAccount(address, provider))

    def disconnect_from_clef(self) -> None:
        """
        Disconnect from Clef.

        Removes all `ClefAccount` objects from the container.
        """
        self._accounts = [i for i in self._accounts if not isinstance(i, ClefAccount)]


class PublicKeyAccount:
    """Class for interacting with an Ethereum account where you do not control
    the private key. Can be used to check the balance or nonce, and to send ether to."""

    def __init__(self, addr: str) -> None:
        self.address = _resolve_address(addr)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} '{self.address}'>"

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
        balance = web3.eth.get_balance(self.address)
        return Wei(balance)

    @property
    def gas_used(self) -> int:
        """Returns the cumulative gas amount paid from this account."""
        return sum(i.gas_used for i in history.from_sender(self.address))

    @property
    def nonce(self) -> int:
        return web3.eth.get_transaction_count(self.address)

    def get_deployment_address(self, nonce: Optional[int] = None) -> EthAddress:
        """
        Return the address of a contract deployed from this account at the given nonce.

        Arguments
        ---------
        nonce : int, optional
            The nonce of the deployment transaction. If not given, the nonce of the next
            transaction is used.
        """
        if nonce is None:
            nonce = self.nonce

        address = HexBytes(self.address)
        raw = rlp.encode([address, nonce])
        deployment_address = keccak(raw)[12:]

        return EthAddress(deployment_address)


class _PrivateKeyAccount(PublicKeyAccount):
    """Base class for Account and LocalAccount"""

    def __init__(self, addr: str) -> None:
        self._lock = threading.Lock()
        super().__init__(addr)

    def _pending_nonce(self) -> int:
        tx_from_sender = sorted(history.from_sender(self.address), key=lambda k: k.nonce)
        if len(tx_from_sender) == 0:
            return self.nonce

        last_tx = tx_from_sender[-1]
        if last_tx.status == -1:
            return last_tx.nonce + 1

        nonce = self.nonce
        while nonce == last_tx.nonce:
            # ganache does not always immediately increment the nonce
            time.sleep(0.5)
            nonce = self.nonce

        return nonce

    def _gas_limit(
        self,
        to: Optional["Account"],
        amount: int,
        gas_price: Optional[int],
        gas_buffer: Optional[float],
        data: Optional[str] = None,
    ) -> int:
        gas_limit = CONFIG.active_network["settings"]["gas_limit"]
        if gas_limit == "max":
            return Chain().block_gas_limit

        if isinstance(gas_limit, bool) or gas_limit in (None, "auto"):
            gas_buffer = gas_buffer or CONFIG.active_network["settings"]["gas_buffer"]
            gas_limit = self.estimate_gas(to, amount, 0, data or "")
            if gas_limit > 21000 and gas_buffer != 1:
                gas_limit = Wei(gas_limit * gas_buffer)
                return min(gas_limit, Chain().block_gas_limit)

        return Wei(gas_limit)

    def _gas_price(self, gas_price: Any = None) -> Tuple[Wei, Optional[GasABC], Optional[Iterator]]:
        # returns the gas price, gas strategy object, and active gas strategy iterator
        if gas_price is None:
            gas_price = CONFIG.active_network["settings"]["gas_price"]

        if isinstance(gas_price, GasABC):
            value = gas_price.get_gas_price()
            if isinstance(value, Iterator):
                # if `get_gas_price` returns an interator, this is a gas strategy
                # intended for rebroadcasting. we need to retain both the strategy
                # object and the active gas price iterator
                return Wei(next(value)), gas_price, value
            else:
                # for simple strategies, we can simply use the generated gas price
                return Wei(value), None, None

        if isinstance(gas_price, Wei):
            return gas_price, None, None

        if isinstance(gas_price, bool) or gas_price in (None, "auto"):
            return web3.eth.generate_gas_price(), None, None

        return Wei(gas_price), None, None

    def _check_for_revert(self, tx: Dict) -> None:
        try:
            # remove gas price related values to avoid issues post-EIP1559
            # https://github.com/ethereum/go-ethereum/pull/23027
            skip_keys = {"gasPrice", "maxFeePerGas", "maxPriorityFeePerGas"}
            web3.eth.call({k: v for k, v in tx.items() if k not in skip_keys and v})
        except ValueError as exc:
            exc = VirtualMachineError(exc)
            raise ValueError(
                f"Execution reverted during call: '{exc.revert_msg}'. This transaction will likely "
                "revert. If you wish to broadcast, include `allow_revert:True` as a parameter.",
            ) from None

    def deploy(
        self,
        contract: Any,
        *args: Tuple,
        amount: int = 0,
        gas_limit: Optional[int] = None,
        gas_buffer: Optional[float] = None,
        gas_price: Optional[int] = None,
        max_fee: Optional[int] = None,
        priority_fee: Optional[int] = None,
        nonce: Optional[int] = None,
        required_confs: int = 1,
        allow_revert: bool = None,
        silent: bool = None,
        publish_source: bool = False,
    ) -> Any:
        """Deploys a contract.

        Args:
            contract: ContractContainer instance.
            *args: Constructor arguments. The last argument may optionally be
                   a dictionary of transaction values.

        Kwargs:
            amount: Amount of ether to send with transaction, in wei.
            gas_limit: Gas limit of the transaction.
            gas_buffer: Multiplier to apply to gas limit.
            gas_price: Gas price of legacy transaction.
            max_fee: Max fee per gas of dynamic fee transaction.
            priority_fee: Max priority fee per gas of dynamic fee transaction.
            nonce: Nonce to use for the transaction.

        Returns:
            * Contract instance if the transaction confirms and the contract exists
            * TransactionReceipt if the transaction is pending or reverts
        """
        data = contract.deploy.encode_input(*args)
        receipt, exc = self._make_transaction(
            None,
            amount,
            gas_limit,
            gas_buffer,
            gas_price,
            max_fee,
            priority_fee,
            data,
            nonce,
            contract._name + ".constructor",
            required_confs,
            allow_revert,
            silent,
        )

        add_thread = threading.Thread(target=contract._add_from_tx, args=(receipt,), daemon=True)
        add_thread.start()

        if rpc.is_active():
            undo_thread = threading.Thread(
                target=Chain()._add_to_undo_buffer,
                args=(
                    receipt,
                    self.deploy,
                    (contract, *args),
                    {
                        "amount": amount,
                        "gas_limit": gas_limit,
                        "gas_buffer": gas_buffer,
                        "gas_price": gas_price,
                        "max_fee": max_fee,
                        "priority_fee": priority_fee,
                    },
                ),
                daemon=True,
            )
            undo_thread.start()

        if receipt.status != 1:
            receipt._raise_if_reverted(exc)
            return receipt

        add_thread.join()
        try:
            deployed_contract = contract.at(receipt.contract_address)
            if publish_source:
                contract.publish_source(deployed_contract, silent=silent)
            return deployed_contract
        except ContractNotFound:
            # if the contract self-destructed during deployment
            return receipt

    def estimate_gas(
        self, to: "Account" = None, amount: int = 0, gas_price: int = None, data: str = None
    ) -> int:
        """
        Estimate the gas cost for a transaction.

        Raises VirtualMachineError if the transaction would revert.

        Arguments
        ---------
        to : Account, optional
            Account instance or address string of transaction recipient.
        amount : int, optional
            Amount of ether to send in wei.
        gas_price : int, optional
            Gas price of the transaction.
        data : str, optional
            Transaction data hexstring.

        Returns
        -------
        Estimated gas value in wei.
        """
        tx: Dict = {
            "from": self.address,
            "to": to_address(str(to)) if to else None,
            "value": Wei(amount),
            "data": HexBytes(data or ""),
        }
        if gas_price is not None:
            tx["gasPrice"] = web3.to_hex(gas_price)
        try:
            return web3.eth.estimate_gas(tx)
        except ValueError as exc:
            revert_gas_limit = CONFIG.active_network["settings"]["reverting_tx_gas_limit"]
            if revert_gas_limit == "max":
                revert_gas_limit = web3.eth.get_block("latest")["gasLimit"]
                CONFIG.active_network["settings"]["reverting_tx_gas_limit"] = revert_gas_limit
            if revert_gas_limit:
                return revert_gas_limit

            exc = VirtualMachineError(exc)
            raise ValueError(
                f"Gas estimation failed: '{exc.revert_msg}'. This transaction will likely revert. "
                "If you wish to broadcast, you must set the gas limit manually."
            )

    def transfer(
        self,
        to: "Account" = None,
        amount: int = 0,
        gas_limit: Optional[int] = None,
        gas_buffer: Optional[float] = None,
        gas_price: Optional[int] = None,
        max_fee: Optional[int] = None,
        priority_fee: Optional[int] = None,
        data: str = None,
        nonce: Optional[int] = None,
        required_confs: int = 1,
        allow_revert: bool = None,
        silent: bool = None,
    ) -> TransactionReceipt:
        """
        Broadcast a transaction from this account.

        Kwargs:
            to: Account instance or address string to transfer to.
            amount: Amount of ether to send, in wei.
            gas_limit: Gas limit of the transaction.
            gas_buffer: Multiplier to apply to gas limit.
            gas_price: Gas price of legacy transaction.
            max_fee: Max fee per gas of dynamic fee transaction.
            priority_fee: Max priority fee per gas of dynamic fee transaction.
            nonce: Nonce to use for the transaction.
            data: Hexstring of data to include in transaction.
            silent: Toggles console verbosity.

        Returns:
            TransactionReceipt object
        """

        receipt, exc = self._make_transaction(
            to,
            amount,
            gas_limit,
            gas_buffer,
            gas_price,
            max_fee,
            priority_fee,
            data or "",
            nonce,
            "",
            required_confs,
            allow_revert,
            silent,
        )

        if rpc.is_active():
            undo_thread = threading.Thread(
                target=Chain()._add_to_undo_buffer,
                args=(
                    receipt,
                    self.transfer,
                    [],
                    {
                        "to": to,
                        "amount": amount,
                        "gas_limit": gas_limit,
                        "gas_buffer": gas_buffer,
                        "gas_price": gas_price,
                        "max_fee": max_fee,
                        "priority_fee": priority_fee,
                        "data": data,
                    },
                ),
                daemon=True,
            )
            undo_thread.start()

        receipt._raise_if_reverted(exc)
        return receipt

    def _make_transaction(
        self,
        to: Optional["Account"],
        amount: int,
        gas_limit: Optional[int],
        gas_buffer: Optional[float],
        gas_price: Optional[int],
        max_fee: Optional[int],
        priority_fee: Optional[int],
        data: str,
        nonce: Optional[int],
        fn_name: str,
        required_confs: int,
        allow_revert: Optional[bool],
        silent: Optional[bool],
    ) -> Tuple[TransactionReceipt, Optional[Exception]]:
        # shared logic for `transfer` and `deploy`
        if gas_limit and gas_buffer:
            raise ValueError("Cannot set gas_limit and gas_buffer together")
        if silent is None:
            silent = bool(CONFIG.mode == "test" or CONFIG.argv["silent"])

        if gas_price is None:
            # if gas price is not explicitly set, load the default max fee and priority fee
            if max_fee is None:
                max_fee = CONFIG.active_network["settings"]["max_fee"] or None
            if priority_fee is None:
                priority_fee = CONFIG.active_network["settings"]["priority_fee"] or None

        if priority_fee == "auto":
            try:
                priority_fee = Chain().priority_fee
            except ValueError:
                # fallback to legacy transactions if network does not support EIP1559
                CONFIG.active_network["settings"]["priority_fee"] = None
                priority_fee = None

        try:
            # if max fee and priority fee are not set, use gas price
            if max_fee is None and priority_fee is None:
                gas_price, gas_strategy, gas_iter = self._gas_price(gas_price)
            else:
                gas_strategy, gas_iter = None, None
            gas_limit = Wei(gas_limit) or self._gas_limit(
                to, amount, gas_price or max_fee, gas_buffer, data
            )
        except ValueError as e:
            raise VirtualMachineError(e) from None

        with self._lock:
            # we use a lock here to prevent nonce issues when sending many tx's at once
            tx = {
                "from": self.address,
                "value": Wei(amount),
                "nonce": nonce if nonce is not None else self._pending_nonce(),
                "gas": web3.to_hex(gas_limit),
                "data": HexBytes(data),
            }
            if to:
                tx["to"] = to_address(str(to))
            tx = _apply_fee_to_tx(tx, gas_price, max_fee, priority_fee)
            txid = None
            while True:
                try:
                    response = self._transact(tx, allow_revert)  # type: ignore
                    exc, revert_data = None, None
                    if txid is None:
                        txid = HexBytes(response).hex()
                        if not silent:
                            print(f"\rTransaction sent: {color('bright blue')}{txid}{color}")
                except ValueError as e:
                    if txid is None:
                        exc = VirtualMachineError(e)
                        if not hasattr(exc, "txid"):
                            raise exc from None
                        txid = exc.txid
                        print(f"\rTransaction sent: {color('bright blue')}{txid}{color}")
                        revert_data = (exc.revert_msg, exc.pc, exc.revert_type)
                try:
                    receipt = TransactionReceipt(
                        txid,
                        self,
                        silent=silent,
                        required_confs=required_confs,
                        is_blocking=False,
                        name=fn_name,
                        revert_data=revert_data,
                    )  # type: ignore
                    break
                except (TransactionNotFound, ValueError):
                    if not silent:
                        sys.stdout.write(f"  Awaiting transaction in the mempool... {_marker[0]}\r")
                        sys.stdout.flush()
                        _marker.rotate(1)
                    time.sleep(1)

        receipt = self._await_confirmation(receipt, required_confs, gas_strategy, gas_iter)
        if receipt.status != 1 and exc is None:
            error_data = {
                "message": (
                    f"VM Exception while processing transaction: revert {receipt.revert_msg}"
                ),
                "code": -32000,
                "data": {
                    receipt.txid: {
                        "error": "revert",
                        "program_counter": receipt._revert_pc,
                        "return": receipt.return_value,
                        "reason": receipt.revert_msg,
                    },
                },
            }
            exc = VirtualMachineError(ValueError(error_data))

        return receipt, exc

    def _await_confirmation(
        self,
        receipt: TransactionReceipt,
        required_confs: int,
        gas_strategy: Optional[GasABC],
        gas_iter: Optional[Iterator],
    ) -> TransactionReceipt:
        # add to TxHistory before waiting for confirmation, this way the tx
        # object is available if the user exits blocking via keyboard interrupt
        history._add_tx(receipt)

        if gas_strategy is not None:
            gas_strategy.run(receipt, gas_iter)  # type: ignore

        if required_confs == 0:
            # set 0-conf tx's as silent to hide the confirmation output
            receipt._silent = True
            return receipt

        try:
            receipt._confirmed.wait()
        except KeyboardInterrupt as exc:
            # set related transactions as silent
            receipt._silent = True
            for receipt in history.filter(
                sender=self, nonce=receipt.nonce, key=lambda k: k.status != -2
            ):
                receipt._silent = True
            raise exc.with_traceback(None)

        if receipt.status != -2:
            return receipt

        # if transaction was dropped (status -2), find and return the tx that confirmed
        replacements = history.filter(
            sender=self, nonce=receipt.nonce, key=lambda k: k.status != -2
        )
        while True:
            if not replacements:
                raise TransactionError(f"Tx dropped without known replacement: {receipt.txid}")
            if len(replacements) > 1:
                # in case we have multiple tx's where the status is still unresolved
                replacements = [i for i in replacements if i.status != 2]
                time.sleep(0.5)
            else:
                receipt = replacements[0]
                receipt._await_confirmation(required_confs=required_confs)
                return receipt


class Account(_PrivateKeyAccount):
    """Class for interacting with an Ethereum account.

    Attributes:
        address: Public address of the account.
        nonce: Current nonce of the account."""

    def _transact(self, tx: Dict, allow_revert: bool) -> Any:
        if allow_revert is None:
            allow_revert = bool(CONFIG.network_type == "development")
        if not allow_revert:
            self._check_for_revert(tx)
        return web3.eth.send_transaction(tx)


class LocalAccount(_PrivateKeyAccount):
    """Class for interacting with an Ethereum account.

    Attributes:
        address: Public address of the account.
        nonce: Current nonce of the account.
        private_key: Account private key.
        public_key: Account public key."""

    def __init__(self, address: str, account: Account, priv_key: Union[int, bytes, str]) -> None:
        self._acct = account
        if not isinstance(priv_key, str):
            priv_key = HexBytes(priv_key).hex()
        self.private_key = priv_key
        self.public_key = eth_keys.keys.PrivateKey(HexBytes(priv_key)).public_key
        super().__init__(address)

    def save(self, filename: str, overwrite: bool = False, password: Optional[str] = None) -> str:
        """Encrypts the private key and saves it in a keystore json.

        Attributes:
            filename: path to keystore file. If no folder is given, saved in
                      ~/.brownie/accounts
            overwrite: if True, will overwrite an existing file.
            password: Password used to encrypt the account. If none, you will be prompted

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

        if password is None:
            password = getpass("Enter the password to encrypt this account with: ")

        encrypted = web3.eth.account.encrypt(self.private_key, password)
        encrypted["address"] = encrypted["address"].lower()
        with json_file.open("w") as fp:
            json.dump(encrypted, fp)
        return str(json_file)

    def sign_defunct_message(self, message: str) -> SignedMessage:
        """Signs an `EIP-191` using this account's private key.

        Args:
            message: An text

        Returns:
            An eth_account `SignedMessage` instance.
        """
        msg_hash_bytes = defunct_hash_message(text=message)
        eth_private_key = eth_keys.keys.PrivateKey(HexBytes(self.private_key))
        (v, r, s, eth_signature_bytes) = sign_message_hash(eth_private_key, msg_hash_bytes)
        return SignedMessage(
            messageHash=msg_hash_bytes,
            r=r,
            s=s,
            v=v,
            signature=HexBytes(eth_signature_bytes),
        )

    def sign_message(self, message: EIP712Message) -> SignedMessage:
        """Signs an `EIP712Message` using this account's private key.

        Args:
            message: An `EIP712Message` instance.

        Returns:
            An eth_account `SignedMessage` instance.
        """
        # some of this code is from:
        # https://github.com/ethereum/eth-account/blob/00e7b10/eth_account/account.py#L577
        # https://github.com/ethereum/eth-account/blob/00e7b10/eth_account/account.py#L502
        msg_hash_bytes = HexBytes(_hash_eip191_message(message.signable_message))
        assert len(msg_hash_bytes) == 32, "The message hash must be exactly 32-bytes"
        eth_private_key = eth_keys.keys.PrivateKey(HexBytes(self.private_key))
        (v, r, s, eth_signature_bytes) = sign_message_hash(eth_private_key, msg_hash_bytes)
        return SignedMessage(
            messageHash=msg_hash_bytes,
            r=r,
            s=s,
            v=v,
            signature=HexBytes(eth_signature_bytes),
        )

    def _transact(self, tx: Dict, allow_revert: bool) -> None:
        if allow_revert is None:
            allow_revert = bool(CONFIG.network_type == "development")
        if not allow_revert:
            self._check_for_revert(tx)
        tx["chainId"] = web3.chain_id
        signed_tx = self._acct.sign_transaction(tx).rawTransaction  # type: ignore
        return web3.eth.send_raw_transaction(signed_tx)


class ClefAccount(_PrivateKeyAccount):
    """
    Class for interacting with an Ethereum account where signing is handled in Clef.
    """

    def __init__(self, address: str, provider: Union[HTTPProvider, IPCProvider]) -> None:
        self._provider = provider
        super().__init__(address)

    def _transact(self, tx: Dict, allow_revert: bool) -> None:
        if allow_revert is None:
            allow_revert = bool(CONFIG.network_type == "development")
        if not allow_revert:
            self._check_for_revert(tx)

        formatters = {
            "nonce": web3.to_hex,
            "value": web3.to_hex,
            "chainId": web3.to_hex,
            "data": web3.to_hex,
            "from": to_address,
        }
        if "to" in tx:
            formatters["to"] = to_address

        tx["chainId"] = web3.chain_id
        tx = apply_formatters_to_dict(formatters, tx)

        response = self._provider.make_request("account_signTransaction", [tx])
        if "error" in response:
            raise ValueError(response["error"]["message"])
        return web3.eth.send_raw_transaction(response["result"]["raw"])


def _apply_fee_to_tx(
    tx: Dict,
    gas_price: Optional[int] = None,
    max_fee: Optional[int] = None,
    priority_fee: Optional[int] = None,
) -> Dict:
    tx = tx.copy()

    if gas_price is not None:
        if max_fee or priority_fee:
            raise ValueError("gas_price and (max_fee, priority_fee) are mutually exclusive")
        tx["gasPrice"] = web3.to_hex(gas_price)
        return tx

    if priority_fee is None:
        raise InvalidTransaction("priority_fee must be defined")
    priority_fee = Wei(priority_fee)

    # no max_fee specified, infer from base_fee
    if max_fee is None:
        base_fee = Chain().base_fee
        max_fee = base_fee * 2 + priority_fee
    else:
        max_fee = Wei(max_fee)

    if priority_fee > max_fee:
        raise InvalidTransaction("priority_fee must not exceed max_fee")

    tx["maxFeePerGas"] = web3.to_hex(max_fee)
    tx["maxPriorityFeePerGas"] = web3.to_hex(priority_fee)
    tx["type"] = web3.to_hex(2)
    return tx
