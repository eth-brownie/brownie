.. _api-network:

===========
Network API
===========

The ``network`` package holds classes for interacting with the Ethereum blockchain. This is the most extensive package within Brownie and contains the majority of the user-facing functionality.

``brownie.network.main``
========================

The ``main`` module contains methods for connecting to or disconnecting from the network. All of these methods are available directly from ``brownie.network``.

.. py:method:: main.connect(network = None, launch_rpc = True)

    Connects to a network.

    * ``network``: The network to connect to. If ``None``, connects to the default network as specified in the config file.
    * ``launch_rpc``: If ``True`` and the configuration for this network includes ``test_rpc`` settings, attempts to launch or attach to a local RPC client.

    Calling this method is favored over calling :func:`web3.connect <Web3.connect>` and :func:`rpc.launch <Rpc.launch>` or :func:`rpc.attach <Rpc.attach>` individually.

    .. code-block:: python

        >>> from brownie import network
        >>> network.connect('development')

.. py:method:: main.disconnect(kill_rpc = True)

    Disconnects from the network.

    The :func:`Web3 <brownie.network.web3.Web3>` provider is cleared, the active network is set to ``None`` and the local RPC client is terminated if it was launched as a child process.

    .. code-block:: python

        >>> from brownie import network
        >>> network.disconnect()

.. py:method:: main.is_connected() -> bool

    Returns ``True`` if the :func:`Web3 <brownie.network.web3.Web3>` object is connected to the network.

    .. code-block:: python

        >>> from brownie import network
        >>> network.is_connected()
        True

.. py:method:: main.show_active()

    Returns the name of the network that is currently active, or ``None`` if not connected.

    .. code-block:: python

        >>> from brownie import network
        >>> network.show_active()
        'development'

.. py:method:: main.gas_limit(*args)

    Gets and optionally sets the default gas limit.

    * If no argument is given, the current default is displayed.
    * If an integer value is given, this will be the default gas limit.
    * If set to ``"auto"``, the gas limit is determined automatically via :meth:`web3.eth.estimate_gas <web3.eth.Eth.estimate_gas>`.

    Returns ``False`` if the gas limit is set automatically, or an ``int`` if it is set to a fixed value.

    .. code-block:: python

        >>> from brownie import network
        >>> network.gas_limit()
        False
        >>> network.gas_limit(6700000)
        6700000
        >>> network.gas_limit("auto")
        False

.. py:method:: main.gas_buffer(*args)

    Gets and optionally sets the default gas buffer.

    * If no argument is given, the current default is displayed.
    * If an integer or float value is given, this will be the default gas buffer.
    * If ``None`` is given, the gas buffer is set to ``1`` (disabled).

    .. code-block:: python

        >>> from brownie import network
        >>> network.gas_buffer()
        1.1
        >>> network.gas_buffer(1.25)
        1.25
        >>> network.gas_buffer(None)
        1

.. py:method:: main.gas_price(*args)

    Gets and optionally sets the default gas price.

    * If an integer value is given, this will be the default gas price.
    * If set to ``"auto"``, the gas price is determined automatically via :attr:`web3.eth.gas_price <web3.eth.Eth.gas_price>`.

    Returns ``False`` if the gas price is set automatically, or an ``int`` if it is set to a fixed value.

    .. code-block:: python

        >>> from brownie import network
        >>> network.gas_price()
        False
        >>> network.gas_price(10000000000)
        10000000000
        >>> network.gas_price("1.2 gwei")
        1200000000
        >>> network.gas_price("auto")
        False

.. py:method:: main.max_fee(*args)

    Gets and optionally sets the default max fee per gas.

    * If an integer value is given, this will be the default max fee.
    * If set to ``None`` or ``False``, transactions will instead default to using a legacy-style ``gas_price``.

    .. code-block:: python

        >>> from brownie import network
        >>> network.max_fee()
        None
        >>> network.max_fee(10000000000)
        10000000000
        >>> network.max_fee("45 gwei")
        45000000000

.. py:method:: main.priority_fee(*args)

    Gets and optionally sets the default max priority fee per gas.

    * If an integer value is given, this will be the default priority fee.
    * If set to ``"auto"``, the fee is determined automatically via :attr:`web3.eth.max_priority_fee <web3.eth.Eth.max_priority_fee>`.
    * If set to ``None`` or ``False``, transactions will instead default to using a legacy-style ``gas_price``.

    .. code-block:: python

        >>> from brownie import network
        >>> network.priority_fee()
        None
        >>> network.priority_fee(4000000000)
        4000000000
        >>> network.priority_fee("2 gwei")
        2000000000

``brownie.network.account``
===========================

The ``account`` module holds classes for interacting with Ethereum accounts for which you control the private key.

Classes in this module are not meant to be instantiated directly. The :func:`Accounts <brownie.network.account.Accounts>` container is available as ``accounts`` (or just ``a``) and will create each :func:`Account <brownie.network.account.Account>` automatically during initialization. Add more accounts using :func:`Accounts.add <Accounts.add>`.

Accounts
--------

.. py:class:: brownie.network.account.Accounts

    List-like :func:`Singleton <brownie._singleton._Singleton>` container that holds all of the available accounts as :func:`Account <brownie.network.account.Account>` or :func:`LocalAccount <brownie.network.account.LocalAccount>` objects. When printed it will display as a list.

    .. code-block:: python

        >>> from brownie.network import accounts
        >>> accounts
        [<Account object '0x7Ebaa12c5d1EE7fD498b51d4F9278DC45f8D627A'>, <Account object '0x186f79d227f5D819ACAB0C529031036D11E0a000'>, <Account object '0xC53c27492193518FE9eBff00fd3CBEB6c434Cf8b'>, <Account object '0x2929AF7BBCde235035ED72029c81b71935c49e94'>, <Account object '0xb93538FEb07b3B8433BD394594cA3744f7ee2dF1'>, <Account object '0x1E563DBB05A10367c51A751DF61167dE99A4d0A7'>, <Account object '0xa0942deAc0885096D8400D3369dc4a2dde12875b'>, <Account object '0xf427a9eC1d510D77f4cEe4CF352545071387B2e6'>, <Account object '0x2308D528e4930EFB4aF30793A3F17295a0EFa886'>, <Account object '0x2fb37EB570B1eE8Eda736c1BD1E82748Ec3d0Bf1'>]
        >>> dir(accounts)
        [add, at, clear, load, remove]

Accounts Attributes
*******************

.. py:attribute:: Accounts.default

    Default account that is used for deploying contracts.  Initially set to ``None``.

    Note that the default account used to send contract transactions is the one that deployed the contract, not ``accounts.default``.

    .. code-block:: python

        >>> accounts.default = accounts[1]


Accounts Methods
****************

.. py:classmethod:: Accounts.add(private_key=None)

    Creates a new :func:`LocalAccount <brownie.network.account.LocalAccount>` with private key ``private_key``, appends it to the container, and returns the new account instance.

    .. code-block:: python

        >>> accounts.add('8fa2fdfb89003176a16b707fc860d0881da0d1d8248af210df12d37860996fb2')
        <Account object '0xc1826925377b4103cC92DeeCDF6F96A03142F37a'>

    When no private key is given a new one is randomly generated. A seed phrase for the account is also printed to the console.

    .. code-block:: python

        >>> accounts.add()
        mnemonic: 'buffalo cinnamon glory chalk require inform strike ginger crop sell hidden cart'
        <LocalAccount '0xf293C5E0b22802Bf5DCef3FB8112EaA4cA54fcCF'>

.. py:classmethod:: Accounts.at(address, force=False)

    Given an address as a string, returns the corresponding :func:`Account <brownie.network.account.Account>` or :func:`LocalAccount <brownie.network.account.LocalAccount>` from the container.
    If ``force=True``, returns and adds the account even if it is not found in the container. Use this if an account is unlocked by external means.

    .. code-block:: python

        >>> accounts.at('0xc1826925377b4103cC92DeeCDF6F96A03142F37a')
        <Account object '0xc1826925377b4103cC92DeeCDF6F96A03142F37a'>

.. py:classmethod:: Accounts.clear()

    Empties the container.

    .. code-block:: python

        >>> accounts.clear()

.. py:classmethod:: Accounts.from_mnemonic(mnemonic, count=1, offset=0)

    Generates one or more :func:`LocalAccount <brownie.network.account.LocalAccount>` objects from a seed phrase.

    * ``mnemonic`` : Space-separated list of BIP39 mnemonic seed words
    * ``count`` : The number of `LocalAccount` objects to create
    * ``offset`` : The initial account index to create accounts from

    If ``count`` is greater than 1, a list of :func:`LocalAccount <brownie.network.account.LocalAccount>` objects are returned.

    .. code-block:: python

        >>> a.from_mnemonic('buffalo cinnamon glory chalk require inform strike ginger crop sell hidden cart')
        <LocalAccount '0xf293C5E0b22802Bf5DCef3FB8112EaA4cA54fcCF'>

.. py:classmethod:: Accounts.load(filename=None)

    Decrypts a `keystore <https://github.com/ethereum/wiki/wiki/Web3-Secret-Storage-Definition>`_ file and returns a :func:`LocalAccount <brownie.network.account.LocalAccount>` object.

    Brownie will first attempt to find the keystore file as a path relative to the loaded project. If not found, it will look in the ``brownie/data/accounts`` folder within the Brownie package.

    If filename is ``None``, returns a list of available keystores in ``brownie/data/accounts``.

    .. code-block:: python

        >>> accounts.load()
        ['my_account']
        >>> accounts.load('my_account')
        Enter the password for this account:
        <LocalAccount object '0xa9c2DD830DfFE8934fEb0A93BAbcb6e823e1FF05'>

.. py:classmethod:: Accounts.remove(address)

    Removes an address from the container. The address may be given as a string or an :func:`Account <brownie.network.account.Account>` instance.

    .. code-block:: python

        >>> accounts.remove('0xc1826925377b4103cC92DeeCDF6F96A03142F37a')

.. py:classmethod:: Accounts.connect_to_clef(uri=None, timeout=120)

    Connect to clef and add unlocked accounts to the container as :func:`ClefAccount <brownie.network.account.ClefAccount>` objects.

    `Clef <https://geth.ethereum.org/docs/clef/tutorial>`_ is an account signing utility packaged with Geth, which can be used to interact with hardware wallets in Brownie. Before calling this function, Clef must be running and unlocked in another command prompt.

    * ``uri``: IPC path or http url to use to connect to clef. If ``None``, uses clef's default IPC path on Unix systems or ``http://localhost:8550/`` on Windows.
    * ``timeout``: The number of seconds to wait for clef to respond to a request before raising a ``TimeoutError``.

    .. code-block:: python

        >>> accounts
        []
        >>> accounts.connect_to_clef()
        >>> accounts
        [<ClefAccount object '0x716E8419F2926d6AcE07442675F476ace972C580'>]

.. py:classmethod:: Accounts.disconnect_from_clef()

    Disconnect from Clef.

    Removes all :func:`ClefAccount <brownie.network.account.ClefAccount>` objects from the container.


Accounts Internal Methods
*************************

.. py:classmethod:: Accounts._reset()

    Called by :func:`state._notify_registry <brownie.network.state._notify_registry>` when the local chain has been reset. All :func:`Account <brownie.network.account.Account>` objects are recreated.

.. py:classmethod:: Accounts._revert(height)

    Called by :func:`state._notify_registry <brownie.network.state._notify_registry>` when the local chain has been reverted to a block height greater than zero. Adjusts :func:`Account <brownie.network.account.Account>` object nonce values.

Account
-------

.. py:class:: brownie.network.account.Account

    An ethereum address that you control the private key for, and so can send transactions from. Generated automatically from :attr:`web3.eth.accounts <web3.eth.Eth.accounts>` and stored in the :func:`Accounts <brownie.network.account.Accounts>` container.

    .. code-block:: python

        >>> accounts[0]
        <Account object '0x7Ebaa12c5d1EE7fD498b51d4F9278DC45f8D627A'>
        >>> dir(accounts[0])
        [address, balance, deploy, estimate_gas, nonce, transfer]

Account Attributes
******************

.. py:attribute:: Account.address

    The public address of the account. Viewable by printing the class, you do not need to call this attribute directly.

    .. code-block:: python

        >>> accounts[0].address
        '0x7Ebaa12c5d1EE7fD498b51d4F9278DC45f8D627A'

.. py:attribute:: Account.gas_used

    The cumulative gas amount paid for transactions from this account.

    .. code-block:: python

        >>> accounts[0].gas_used
        21000

.. py:attribute:: Account.nonce

    The current nonce of the address.

    .. code-block:: python

        >>> accounts[0].nonce
        1

Account Methods
***************

.. py:classmethod:: Account.balance()

    Returns the current balance at the address, in :func:`Wei <brownie.convert.datatypes.Wei>`.

    .. code-block:: python

        >>> accounts[0].balance()
        100000000000000000000
        >>> accounts[0].balance() == "100 ether"
        True

.. py:classmethod:: Account.deploy(contract, *args, amount=None, gas_limit=None, gas_price=None, max_fee=None, priority_fee=None, nonce=None, required_confs=1, allow_revert=False, silent=False, publish_source=False,)

    Deploys a contract.

    * ``contract``: A :func:`ContractContainer <brownie.network.contract.ContractContainer>` instance of the contract to be deployed.
    * ``*args``: Contract constructor arguments.
    * ``amount``: Amount of ether to send with the transaction. The given value is converted to :func:`Wei <brownie.convert.datatypes.Wei>`.
    * ``gas_limit``: Gas limit for the transaction. The given value is converted to :func:`Wei <brownie.convert.datatypes.Wei>`. If none is given, the price is set using :meth:`web3.eth.estimate_gas <web3.eth.Eth.estimateGas>`.
    * ``gas_buffer``: A multiplier applied to :meth:`web3.eth.estimate_gas <web3.eth.Eth.estimateGas>` when setting gas limit automatically. ``gas_limit`` and ``gas_buffer`` cannot be given at the same time.
    * ``gas_price``: Gas price for legacy transaction. The given value is converted to :func:`Wei <brownie.convert.datatypes.Wei>`. If none is given, the price is set using :attr:`web3.eth.gas_price <web3.eth.Eth.gasPrice>`.
    * ``max_fee``: Max fee per gas of dynamic fee transaction.
    * ``priority_fee``: Max priority fee per gas of dynamic fee transaction.
    * ``nonce``: Nonce for the transaction. If none is given, the nonce is set using :meth:`web3.eth.get_transaction_count <web3.eth.Eth.getTransactionCount>` while also considering any pending transactions of the Account.
    * ``required_confs``: The required :attr:`confirmations<TransactionReceipt.confirmations>` before the :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` is processed. If none is given, defaults to 1 confirmation.  If 0 is given, immediately returns a pending :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` instead of a :func:`Contract <brownie.network.contract.Contract>` instance, while waiting for a confirmation in a separate thread.
    * ``allow_revert``: When ``True``, forces the deployment of a contract, even if a revert reason is detected.
    * ``silent``: When ``True``, suppresses any console output for the deployment.
    * ``publish_source``: When ``True``, attempts to verify the source code on etherscan.io.

    Returns a :func:`Contract <brownie.network.contract.Contract>` instance upon success. If the transaction reverts or you do not wait for a confirmation, a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` is returned instead.

    .. code-block:: python

        >>> Token
        []
        >>> t = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")

        Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
        Transaction confirmed - block: 1   gas spent: 594186
        Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
        <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
        >>>
        >>> t
        <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
        >>> Token
        [<Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>]
        >>> Token[0]
        <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

.. py:classmethod:: Account.estimate_gas(to=None, amount=0, gas_price=None, data="")

    Estimates the gas required to perform a transaction. Raises a func:`VirtualMachineError <brownie.exceptions.VirtualMachineError>` if the transaction would revert.

    The returned value is given as an ``int`` denominated in wei.

    * ``to``: Recipient address. Can be an :func:`Account <brownie.network.account.Account>` instance or string.
    * ``amount``: Amount of ether to send. The given value is converted to :func:`Wei <brownie.convert.datatypes.Wei>`.
    * ``gas_price``: Gas price of the transaction.
    * ``data``: Transaction data hexstring.

    .. code-block:: python

        >>> accounts[0].estimate_gas(accounts[1], "1 ether")
        21000

.. py:classmethod:: Account.get_deployment_address(nonce=None)

    Return the address where a contract will be deployed from this account, if the deployment transaction uses the given nonce.

    If nonce is `None`, the nonce of the next transaction is used.

    .. code-block:: python

        >>> accounts[0].get_deployment_address()
        '0xd495633B90a237de510B4375c442C0469D3C161C'

.. py:classmethod:: Account.transfer(self, to=None, amount=0, gas_limit=None, gas_price=None, max_fee=None, priority_fee=None, data=None, nonce=None, required_confs=1, allow_revert=None, silent=False)

    Broadcasts a transaction from this account.

    * ``to``: Recipient address. Can be an :func:`Account <brownie.network.account.Account>` instance or string.
    * ``amount``: Amount of ether to send. The given value is converted to :func:`Wei <brownie.convert.datatypes.Wei>`.
    * ``gas_limit``: Gas limit for the transaction. The given value is converted to :func:`Wei <brownie.convert.datatypes.Wei>`. If none is given, the price is set using :meth:`web3.eth.estimate_gas <web3.eth.Eth.estimateGas>`.
    * ``gas_buffer``: A multiplier applied to :meth:`web3.eth.estimate_gas <web3.eth.Eth.estimateGas>` when setting gas limit automatically. ``gas_limit`` and ``gas_buffer`` cannot be given at the same time.
    * ``gas_price``: Gas price for legacy transaction. The given value is converted to :func:`Wei <brownie.convert.datatypes.Wei>`. If none is given, the price is set using :attr:`web3.eth.gas_price <web3.eth.Eth.gasPrice>`.
    * ``max_fee``: Max fee per gas of dynamic fee transaction.
    * ``priority_fee``: Max priority fee per gas of dynamic fee transaction.
    * ``data``: Transaction data hexstring.
    * ``nonce``: Nonce for the transaction. If none is given, the nonce is set using :meth:`web3.eth.get_transaction_count <web3.eth.Eth.getTransactionCount>` while also considering any pending transactions of the Account.
    * ``required_confs``: The required :attr:`confirmations<TransactionReceipt.confirmations>` before the :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` is processed. If none is given, defaults to 1 confirmation.  If 0 is given, immediately returns a pending :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>`, while waiting for a confirmation in a separate thread.
    * ``allow_revert``: Boolean indicating whether the transaction should be broadcasted when it is expected to revert. If not set, the default behaviour is to allow reverting transactions in development and disallow them in a live environment.
    * ``silent``: Toggles console verbosity. If ``True`` is given, suppresses all console output for this transaction.

    Returns a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` instance.

    .. code-block:: python

        >>> accounts[0].transfer(accounts[1], "1 ether")

        Transaction sent: 0x0173aa6938c3a5e50b6dc7b4d38e16dab40811ab4e00e55f3e0d8be8491c7852
        Transaction confirmed - block: 1   gas used: 21000 (100.00%)
        <Transaction object '0x0173aa6938c3a5e50b6dc7b4d38e16dab40811ab4e00e55f3e0d8be8491c7852'>

    You can also deploy contracts by omitting the ``to`` field. Note that deploying with this method does not automatically create a :func:`Contract <brownie.network.contract.Contract>` object.

    .. code-block:: python

        >>> deployment_bytecode = "0x6103f056600035601c52740100..."
        >>> accounts[0].transfer(data=deployment_bytecode)
        Transaction sent: 0x2b33315f7f9ec86d27112ea6dffb69b6eea1e582d4b6352245c0ac8e614fe06f
          Gas price: 0.0 gwei   Gas limit: 6721975
          Transaction confirmed - Block: 1   Gas used: 268460 (3.99%)
          UnknownContract deployed at: 0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87
        <Transaction '0x2b33315f7f9ec86d27112ea6dffb69b6eea1e582d4b6352245c0ac8e614fe06f'>

LocalAccount
------------

.. py:class:: brownie.network.account.LocalAccount

    Functionally identical to :func:`Account <brownie.network.account.Account>`. The only difference is that a ``LocalAccount`` is one where the private key was directly inputted, and so is not found in :attr:`web3.eth.accounts <web3.eth.Eth.accounts>`.

    .. note:: Resetting the RPC client will delete all ``LocalAccount`` objects from the :func:`Account <brownie.network.account.Accounts>` container.

    .. code-block:: python

        >>> accounts.add()
        <LocalAccount object '0x716E8419F2926d6AcE07442675F476ace972C580'>
        >>> accounts[-1]
        <LocalAccount object '0x716E8419F2926d6AcE07442675F476ace972C580'>

LocalAccount Attributes
***********************

.. py:attribute:: LocalAccount.public_key

    The local account's public key as a string.

    .. code-block:: python

        >>> accounts[-1].public_key
        '0x34b51e2913f5771acdddea7d353404f844b02a39ad4003c08afaa729993c43e890181327beaf352d81424cd277f4badc55be789a2817ea097bc82ea4801fee5b'

.. py:attribute:: LocalAccount.private_key

    The local account's private key as a string.

    .. code-block:: python

        >>> accounts[-1].private_key
        '0xd289bec8d9ad145aead13911b5bbf01936cbcd0efa0e26d5524b5ad54a61aeb8'

LocalAccount Methods
********************

.. py:classmethod:: LocalAccount.save(filename, overwrite=False)

    Saves the account's private key in an encrypto `keystore <https://github.com/ethereum/wiki/wiki/Web3-Secret-Storage-Definition>`_ file.

    If the filename does not include a folder, the keystore is saved in the ``brownie/data/accounts`` folder within the Brownie package.

    Returns the absolute path to the keystore file, as a string.

    .. code-block:: python

        >>> accounts[-1].save('my_account')
        Enter the password to encrypt this account with:
        /python3.6/site-packages/brownie/data/accounts/my_account.json
        >>>
        >>> accounts[-1].save('~/my_account.json')
        Enter the password to encrypt this account with:
        /home/computer/my_account.json

ClefAccount
------------

.. py:class:: brownie.network.account.ClefAccount

    Functionally identical to :func:`Account <brownie.network.account.Account>`. A ``ClefAccount`` object is used for accounts that have been unlocked via `clef <https://geth.ethereum.org/docs/clef/tutorial>`_, and where signing of transactions is handled externally from brownie. This is useful for hardware wallets.

    .. code-block:: python

        >>> accounts
        []
        >>> accounts.connect_to_clef()
        >>> accounts
        [<ClefAccount object '0x716E8419F2926d6AcE07442675F476ace972C580'>]

PublicKeyAccount
----------------

.. py:class:: brownie.network.account.PublicKeyAccount

    Object for interacting with an Ethereum account where you do not control the private key. Can be used to check balances or to send ether to that address.

    .. code-block:: python

        >>> from brownie.network.account import PublicKeyAccount
        >>> pub = PublicKeyAccount("0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E")
        <PublicKeyAccount object '0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E'>

    Along with regular addresses, ``PublicKeyAccount`` objects can be instantiated using `ENS domain names <https://ens.domains/>`_. The returned object will have the resolved address.

    .. code-block:: python

        >>> PublicKeyAccount("ens.snakecharmers.eth")
        <PublicKeyAccount object '0x808B53bF4D70A24bA5cb720D37A4835621A9df00'>

.. py:classmethod:: PublicKeyAccount.balance()

    Returns the current balance at the address, in :func:`Wei <brownie.convert.datatypes.Wei>`.

    .. code-block:: python

        >>> pub.balance()
        1000000000000000000

.. py:attribute:: PublicKeyAccount.nonce

    The current nonce of the address.

    .. code-block:: python

        >>> accounts[0].nonce
        0

``brownie.network.alert``
=========================

The ``alert`` module is used to set up notifications and callbacks based on state changes in the blockchain.

Alert
-----

Alerts and callbacks are handled by creating instances of the ``Alert`` class.

.. py:class:: brownie.network.alert.Alert(fn, args=None, kwargs=None, delay=2, msg=None, callback=None, repeat=False)

    An alert object. It is active immediately upon creation of the instance.

    * ``fn``: A callable to check for the state change.
    * ``args``: Arguments to supply to the callable.
    * ``kwargs``: Keyword arguments to supply to the callable.
    * ``delay``: Number of seconds to wait between checking for changes.
    * ``msg``: String to display upon change. The string will have ``.format(initial_value, new_value)`` applied before displaying.
    * ``callback``: A callback function to call upon a change in value. It should accept two arguments, the initial value and the new value.
    * ``repeat``: If ``False``, the alert will terminate after the first time it first. if ``True``, it will continue to fire with each change until it is stopped via ``Alert.stop()``.  If an ``int`` value is given, it will fire a total of ``n+1`` times before terminating.

    Alerts are **non-blocking**, threading is used to monitor changes. Once an alert has finished running it cannot be restarted.

    A basic example of an alert, watching for a changed balance:

    .. code-block:: python

        >>> from brownie.network.alert import Alert
        >>> Alert(accounts[1].balance, msg="Account 1 balance has changed from {} to {}")
        <brownie.network.alert.Alert object at 0x7f9fd25d55f8>

        >>> alert.show()
        [<brownie.network.alert.Alert object at 0x7f9fd25d55f8>]
        >>> accounts[2].transfer(accounts[1], "1 ether")

        Transaction sent: 0x912d6ac704e7aaac01be159a4a36bbea0dc0646edb205af95b6a7d20945a2fd2
        Transaction confirmed - block: 1   gas spent: 21000
        <Transaction object '0x912d6ac704e7aaac01be159a4a36bbea0dc0646edb205af95b6a7d20945a2fd2'>
        ALERT: Account 1 balance has changed from 100000000000000000000 to 101000000000000000000

    This example uses the alert's callback function to perform a token transfer, and sets a second alert to watch for the transfer:

    .. code-block:: python

        >>> alert.new(accounts[3].balance, msg="Account 3 balance has changed from {} to {}")
        <brownie.network.alert.Alert object at 0x7fc743e415f8>

        >>> def on_receive(old_value, new_value):
        ...     accounts[2].transfer(accounts[3], new_value-old_value)

        >>> alert.new(accounts[2].balance, callback=on_receive)
        <brownie.network.alert.Alert object at 0x7fc743e55cf8>
        >>> accounts[1].transfer(accounts[2],"1 ether")

        Transaction sent: 0xbd1bade3862f181359f32dac02ffd1d145fdfefc99103ca0e3d28ffc7071a9eb
        Transaction confirmed - block: 1   gas spent: 21000
        <Transaction object '0xbd1bade3862f181359f32dac02ffd1d145fdfefc99103ca0e3d28ffc7071a9eb'>

        Transaction sent: 0x8fcd15e38eed0a5c9d3d807d593b0ea508ba5abc892428eb2e0bb0b8f7dc3083
        Transaction confirmed - block: 2   gas spent: 21000
        ALERT: Account 3 balance has changed from 100000000000000000000 to 101000000000000000000

.. py:classmethod:: Alert.is_alive()

    Returns a boolean indicating if an alert is currently running.

    .. code-block:: python

        >>> a.is_alive()
        True

.. py:classmethod:: Alert.wait(timeout=None)

    Blocks until an alert has completed firing or the timeout value is reached. Similar to ``Thread.join()``.

    .. code-block:: python

        >>> a.wait()

.. py:classmethod:: Alert.stop(wait=True)

    Stops the alert.

    .. code-block:: python

        >>> alert_list = alert.show()
        [<brownie.network.alert.Alert object at 0x7f9fd25d55f8>]
        >>> alert_list[0].stop()
        >>> alert.show()
        []

Module Methods
--------------

.. py:method:: alert.new(fn, args=[], kwargs={}, delay=0.5, msg=None, callback=None, repeat=False)

    Alias for creating a new :func:`Alert <brownie.network.alert.Alert>` instance.

    .. code-block:: python

        >>> from brownie import alert
        >>> alert.new(accounts[3].balance, msg="Account 3 balance has changed from {} to {}")
        <brownie.network.alert.Alert object at 0x7fc743e415f8>

.. py:method:: alert.show()

    Returns a list of all currently active alerts.

    .. code-block:: python

        >>> alert.show()
        [<brownie.network.alert.Alert object at 0x7f9fd25d55f8>]

.. py:method:: alert.stop_all()

    Stops all currently active alerts.

    .. code-block:: python

        >>> alert.show()
        [<brownie.network.alert.Alert object at 0x7f9fd25d55f8>]
        >>> alert.stop_all()
        >>> alert.show()
        []

``brownie.network.contract``
============================

The ``contract`` module contains classes for deploying and interacting with smart contracts.

When a project is loaded, Brownie automatically creates :func:`ContractContainer <brownie.network.contract.ContractContainer>` instances from on the files in the ``contracts/`` folder. New :func:`ProjectContract <brownie.network.contract.ProjectContract>` instances are created via methods in the container.

If you wish to interact with a contract outside of a project where only the ABI is available, use the :func:`Contract <brownie.network.contract.Contract>` class.

Arguments supplied to calls or transaction methods are converted using the methods outlined in the :ref:`convert<api-convert>` module.

.. note::

    On networks where persistence is enabled, :func:`ProjectContract <brownie.network.contract.ProjectContract>` instances will remain between sessions. Use :func:`ContractContainer.remove <ContractContainer.remove>` to delete these objects when they are no longer needed. See the documentation on :ref:`persistence<persistence>` for more information.

ContractContainer
-----------------

.. py:class:: brownie.network.contract.ContractContainer

    A list-like container class that holds all :func:`ProjectContract <brownie.network.contract.ProjectContract>` instances of the same type, and is used to deploy new instances of that contract.

    .. code-block:: python

        >>> Token
        []
        >>> dir(Token)
        [abi, at, bytecode, deploy, remove, signatures, topics, tx]

ContractContainer Attributes
****************************

.. py:attribute:: ContractContainer.abi

    The ABI of the contract.

    >>> Token.abi
    [{'constant': True, 'inputs': [], 'name': 'name', 'outputs': [{'name': '', 'type': 'string'}], 'payable': False, 'stateMutability': 'view', 'type': 'function'}, {'constant': False, 'inputs': [{'name': '_spender', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}], 'name': 'approve', 'outputs': [{'name': '', 'type': 'bool'}], 'payable': False, 'stateMutability': 'nonpayable', 'type': 'function'}, ... ]

.. py:attribute:: ContractContainer.bytecode

    The bytecode of the contract, without any applied constructor arguments.

    >>> Token.bytecode
    '608060405234801561001057600080fd5b506040516107873803806107878339810160409081528151602080840151928401516060850151928501805190959490940193909291610055916000918701906100d0565b5082516100699060019060208601906100d0565b50600282905560038190553360008181526004602090815 ...

.. py:attribute:: ContractContainer.signatures

    A dictionary of bytes4 signatures for each contract method.

    If you have a signature and need to find the method name, use :func:`ContractContainer.get_method <ContractContainer.get_method>`.

    .. code-block:: python

        >>> Token.signatures
        {
            'allowance': "0xdd62ed3e",
            'approve': "0x095ea7b3",
            'balanceOf': "0x70a08231",
            'decimals': "0x313ce567",
            'name': "0x06fdde03",
            'symbol': "0x95d89b41",
            'totalSupply': "0x18160ddd",
            'transfer': "0xa9059cbb",
            'transferFrom': "0x23b872dd"
        }
        >>> Token.signatures.keys()
        dict_keys(['name', 'approve', 'totalSupply', 'transferFrom', 'decimals', 'balanceOf', 'symbol', 'transfer', 'allowance'])
        >>> Token.signatures['transfer']
        0xa9059cbb

.. py:attribute:: ContractContainer.topics

    A :py:class:`dict` of bytes32 topics for each contract event.

    .. code-block:: python

        >>> Token.topics
        {
            'Approval': "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",
            'Transfer': "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        }
        >>> Token.topics.keys()
        dict_keys(['Transfer', 'Approval'])
        >>> Token.topics['Transfer']
        0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef

ContractContainer Methods
*************************

.. py:classmethod:: ContractContainer.deploy(*args, publish_source=False)

    Deploys the contract.

    * ``*args``: Contract constructor arguments.
    * ``publish_source``: When ``True``, attempts to verify the source code on etherscan.io.

    You can optionally include a :py:class:`dict` of :ref:`transaction parameters<transaction-parameters>` as the final argument. If you omit this or do not specify a ``'from'`` value, the transaction will be sent from the same address that deployed the contract.

    If the contract requires a library, the most recently deployed one will be used. If the required library has not been deployed yet an `UndeployedLibrary <brownie.exceptions.UndeployedLibrary>` exception is raised.

    Returns a :func:`ProjectContract <brownie.network.contract.ProjectContract>` object upon success.

    In the console if the transaction reverts or you do not wait for a confirmation, a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` is returned instead.

    .. code-block:: python

        >>> Token
        []
        >>> Token.deploy
        <ContractConstructor object 'Token.constructor(string,string,uint256,uint256)'>
        >>> t = Token.deploy("Test Token", "TST", 18, "1000 ether", {'from': accounts[1]})

        Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
        Transaction confirmed - block: 1   gas spent: 594186
        Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
        <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
        >>>
        >>> t
        <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
        >>> Token
        [<Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>]
        >>> Token[0]
        <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

.. py:classmethod:: ContractContainer.at(address, owner=None)

    Returns a new :func:`Contract <brownie.network.contract.ProjectContract>` or :func:`ProjectContract <brownie.network.contract.ProjectContract>` object. The object is also appended to the container.

    * ``address``: Address where the contract is deployed.
    * ``owner``: :func:`Account <brownie.network.account.Account>` instance to set as the contract owner. If transactions to the contract do not specify a ``'from'`` value, they will be sent from this account.

    This method compares the bytecode at the given address with the deployment bytecode for the given :func:`ContractContainer <brownie.network.contract.ContractContainer>`. A :func:`ProjectContract <brownie.network.contract.ProjectContract>` is returned if the bytecodes match, a :func:`Contract <brownie.network.contract.ProjectContract>` otherwise.

    Raises :func:`ContractNotFound <brownie.exceptions.ContractNotFound>` if there is no code at the given address.

    .. code-block:: python

        >>> Token
        [<Token Contract object '0x79447c97b6543F6eFBC91613C655977806CB18b0'>]
        >>> Token.at('0x79447c97b6543F6eFBC91613C655977806CB18b0')
        <Token Contract object '0x79447c97b6543F6eFBC91613C655977806CB18b0'>
        >>> Token.at('0xefb1336a2E6B5dfD83D4f3a8F3D2f85b7bfb61DC')
        File "brownie/lib/console.py", line 82, in _run
            exec('_result = ' + cmd, self.__dict__, local_)
        File "<string>", line 1, in <module>
        File "brownie/lib/components/contract.py", line 121, in at
            raise ValueError("No contract deployed at {}".format(address))
        ValueError: No contract deployed at 0xefb1336a2E6B5dfD83D4f3a8F3D2f85b7bfb61DC

.. py:classmethod:: ContractContainer.publish_source(contract, silent=False)

    Verifies the source code on etherscan.io for a :func:`Project Contract <brownie.network.contract.ProjectContract>` belonging to the container.

    * ``contract``: The :func:`Project Contract <brownie.network.contract.ProjectContract>` you intend to verify
    * ``silent``: When True, suppresses all console output of the call.


.. py:classmethod:: ContractContainer.decode_input(calldata)

    Given the call data of a transaction, returns the function signature as a string and the decoded input arguments.

    Raises ``ValueError`` if the call data cannot be decoded.

    .. code-block:: python

        >>> Token.decode_input('0xa9059cbb0000000000000000000000009dc9431ccccd2c73f0a2f68dc69a4a527ab5d8090000000000000000000000000000000000000000000000000000000000002710')
        ("transfer(address,uint256)", ['0x9DC9431CcCCD2C73F0a2F68Dc69A4a527aB5d809', 10000])

.. py:classmethod:: ContractContainer.get_method(calldata)

    Given the call data of a transaction, returns the name of the contract method as a string.

    .. code-block:: python

        >>> tx = Token[0].transfer(accounts[1], 1000)

        Transaction sent: 0xc1fe0c7c8fd08736718aa9106662a635102604ea6db4b63a319e43474de0b420
        Token.transfer confirmed - block: 3   gas used: 35985 (26.46%)
        <Transaction object '0xc1fe0c7c8fd08736718aa9106662a635102604ea6db4b63a319e43474de0b420'>
        >>> tx.input
        0xa9059cbb00000000000000000000000066ace0365c25329a407002d22908e25adeacb9bb00000000000000000000000000000000000000000000000000000000000003e8
        >>> Token.get_method(tx.input)
        transfer

.. py:classmethod:: ContractContainer.remove(address)

    Removes a contract instance from the container.

    .. code-block:: python

        >>> Token
        [<Token Contract object '0x79447c97b6543F6eFBC91613C655977806CB18b0'>]
        >>> Token.remove('0x79447c97b6543F6eFBC91613C655977806CB18b0')
        >>> Token
        []

ContractContainer Internal Methods
**********************************

.. py:classmethod:: ContractContainer._reset()

    Called by :func:`state._notify_registry <brownie.network.state._notify_registry>` when the local chain has been reset. All :func:`Contract <brownie.network.contract.Contract>` objects are removed from the container and marked as :func:`reverted <Contract._reverted>`.

.. py:classmethod:: ContractContainer._revert(height)

    Called by :func:`state._notify_registry <brownie.network.state._notify_registry>` when the local chain has been reverted to a block height greater than zero. Any :func:`Contract <brownie.network.contract.Contract>` objects that no longer exist are removed from the container and marked as :func:`reverted <Contract._reverted>`.

Contract and ProjectContract
----------------------------

:func:`Contract <brownie.network.contract.Contract>` and :func:`ProjectContract <brownie.network.contract.ProjectContract>` are both used to call or send transactions to smart contracts.

* :func:`Contract <brownie.network.contract.Contract>` objects are instantiated directly. They are used for interaction with already-deployed contracts that exist outside of a project.
* :func:`ProjectContract <brownie.network.contract.ProjectContract>` objects are created by calls to :func:`ContractContainer.deploy <ContractContainer.deploy>`. Because they are compiled and deployed directly by Brownie, they provide greater debugging capability.

These classes have identical APIs.

.. py:class:: brownie.network.contract.Contract(address_or_alias, owner=None)

    A deployed contract that is not part of a Brownie project.

    * ``address_or_alias``: Address of the contract.
    * ``owner``: An optional :func:`Account <brownie.network.account.Account>` instance. If given, transactions to the contract are sent broadcasted from this account by default.

    .. code-block:: python

        >>> from brownie import Contract
        >>> Contract("0x79447c97b6543F6eFBC91613C655977806CB18b0")
        <Token Contract object '0x79447c97b6543F6eFBC91613C655977806CB18b0'>

.. py:class:: brownie.network.contract.ProjectContract

    A deployed contract that is part of an active Brownie project. Along with making calls and transactions, this object allows access to Brownie's full range of debugging and testing capability.

    .. code-block:: python

        >>> Token[0]
        <Token Contract object '0x79447c97b6543F6eFBC91613C655977806CB18b0'>
        >>> dir(Token[0])
        [abi, allowance, approve, balance, balanceOf, bytecode, decimals, name, signatures, symbol, topics, totalSupply, transfer, transferFrom, tx]

.. _api-network-contract-classmethods:

Contract Classmethods
*********************

New ``Contract`` objects are created with one of the following class methods.

.. py:classmethod:: Contract.from_abi(name, address, abi, owner=None)

    Create a new ``Contract`` object from an address and an ABI.

    * ``name``: The name of the contract.
    * ``address``: Address of the contract.
    * ``abi``: ABI of the contract. Required unless a ``manifest_uri`` is given.
    * ``owner``: An optional :func:`Account <brownie.network.account.Account>` instance. If given, transactions to the contract are sent broadcasted from this account by default.

    Creating a ``Contract`` from an ABI will allow you to call or send transactions to the contract, but functionality such as debugging will not be available.

    .. code-block:: python

        >>> from brownie import Contract
        >>> Contract.from_abi("Token", "0x79447c97b6543F6eFBC91613C655977806CB18b0", abi)
        <Token Contract object '0x79447c97b6543F6eFBC91613C655977806CB18b0'>

.. py:classmethod:: Contract.from_explorer(address, as_proxy_for=None, owner=None)

    Create a new ``Contract`` object from source code fetched from a block explorer such as `EtherScan <https://etherscan.io/>`_ or `Blockscout <https://blockscout.com/>`_.

    * ``address``: Address of the contract.
    * ``as_proxy_for``: Address of the implementation contract, if ``address`` is a proxy contract. The generated object sends transactions to ``address``, but uses the ABI and NatSpec of ``as_proxy_for``. This field is only required when the block explorer API does not provide an implementation address.
    * ``owner``: An optional :func:`Account <brownie.network.account.Account>` instance. If given, transactions to the contract are sent broadcasted from this account by default.

    If the deployed bytecode was generated using a compatible compiler version, Brownie will attempt to recompile it locally. If successful, most debugging functionality will be available.

    .. code-block:: python

        >>> Contract.from_explorer("0x6b175474e89094c44da98b954eedeac495271d0f")
        Fetching source of 0x6B175474E89094C44Da98b954EedeAC495271d0F from api.etherscan.io...
        <Dai Contract '0x6B175474E89094C44Da98b954EedeAC495271d0F'>

Contract Attributes
*******************

.. py:attribute:: Contract.alias

    User-defined alias applied to this ``Contract`` object. Can be used to quickly restore the object in future sessions.

    .. code-block:: python

        >>> Token.alias
        'mytoken'

.. py:attribute:: Contract.bytecode

    The bytecode of the deployed contract, including constructor arguments.

    .. code-block:: python

        >>> Token[0].bytecode
        '6080604052600436106100985763ffffffff7c010000000000000000000000000000000000000000000000000000000060003504166306fdde03811461009d578063095ea7b31461012757806318160ddd1461015f57806323b872dd14610186578063313ce567146101b057806370a08231146101c557806395d89b41...

.. py:attribute:: Contract.tx

    The :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` of the transaction that deployed the contract. If the contract was not deployed during this instance of brownie, it will be ``None``.

    .. code-block:: python

        >>> Token[0].tx
        <Transaction object '0xcede03c7e06d2b4878438b08cd0cf4515942b3ba06b3cfd7019681d18bb8902c'>


.. py:attribute:: Contract.events

    The :func:`ContractEvents <brownie.network.contract.ContractEvents>` instance linked to the deployed contract.

    .. code-block:: python

        >>> Token[0].events
        <brownie.network.contract.ContractEvents object at 0x000001CF03C8BB50>

Contract Methods
****************

.. py:classmethod:: Contract.balance()

    Returns the current balance at the contract address, in :func:`Wei <brownie.convert.datatypes.Wei>`.

    .. code-block:: python

        >>> Token[0].balance
        0


.. py:classmethod:: Contract.set_alias(alias)

    Apply a unique alias this object. The alias can be used to restore the object in future sessions.

    * ``alias``: An alias to apply, given as a string. If ``None``, any existing alias is removed.

    Raises ``ValueError`` if the given alias is invalid or already in use on another contract.

    .. code-block:: python

        >>> Token.set_alias('mytoken')

        >>> Token.alias
        'mytoken'


Contract Internal Attributes
****************************

.. py:attribute:: Contract._reverted

    Boolean. Once set to to ``True``, any attempt to interact with the object raises a :func:`ContractNotFound <brownie.exceptions.ContractNotFound>` exception. Set as a result of a call to :func:`state._notify_registry <brownie.network.state._notify_registry>`.

ContractEvents
--------------

:func:`ContractEvents <brownie.network.contract.ContractEvents>` is used to interact with the events of a :func:`Contract <brownie.network.contract.Contract>` or a :func:`ProjectContract <brownie.network.contract.ProjectContract>`.

.. py:class:: brownie.network.contract.ContractEvents(contract=brownie.network.contract.Contract)

    ``ContractEvents`` instances allows you to : subscribe to, listen for or retrieve the different events of a contract.
    This class inherits from the :ref:`web3.py ContractEvents <https://web3py.readthedocs.io/en/stable/contracts.html?highlight=ContractEvents#web3.contract.ContractEvents>` class.

ContractEvents Classmethods
***************************

.. py:classmethod:: ContractEvents.subscribe(event_name, callback, delay=2.0)

    Subscribe to the contract event whose name matches the ``event_name`` parameter.

    * ``event_name``: Name of the event to subscribe to. Must match the exact event name.
    * ``callback``: Function called whenever an event matching 'event_name' occurs, it **must** take one and only one argument which will be the event log receipt.
    * ``delay``: Delay in seconds between each check for new events matching 'event_name'.

    New events are detected and callbacks instructions are executed in sub-threads.

    Each time a new event of this type is detected, creates a new sub-thread to run the ``callback`` function passing the event logs as parameter.

.. py:classmethod:: ContractEvents.get_sequence(from_block, to_block=None, event_type=None)

    Retrieves events emitted by the contract between two blocks.

    * ``from_block``: The block from which to search for events that have occurred.
    * ``to_block``: The block on which to stop searching for events. Defaults to None
    * ``event_type``: Type or name of the event to be searched between the specified blocks. Defaults to None.

    If ``to_block`` is not specified, retrieves events between ``from_block`` and the latest mined block.

    The ``event_type`` parameter can either be a string containing the name of the event to search for or the event type itself (using ``your_contract.events.your_event_name``)

    If ``event_type`` is not passed as parameter, retrieves all contract events between the two blocks.

.. py:classmethod:: ContractEvents.listen(event_name, timeout=0)

    Creates a listening Coroutine object ending whenever an event matching 'event_name' occurs.
    If timeout is superior to zero and no event matching 'event_name' has occured, the Coroutine ends when the timeout is reached.

    * ``event_name``: Name of the event to be listened to.
    * ``timeout``: Timeout value in seconds. Defaults to 0.

    The Coroutine return value is an AttributeDict filled with the following fields :
        - 'event_data' (AttributeDict): The event log receipt that was caught. If no event was caught, evaluates to ``None``
        - 'timed_out' (bool): False if the event did not timeout, else True

    If the 'timeout' parameter is not passed or is inferior or equal to 0, the Coroutine listens until an event occurs.


ContractEvents Attributes
*************************

.. py:attribute:: ContractEvents.linked_contract

    The ``Contract`` object from which the ``ContractEvents`` instance is reading the events.

    .. code-block:: python

        >>> tester
        <BrownieTester Contract '0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87'>
        >>> tester.events.linked_contract
        <BrownieTester Contract '0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87'>

ContractCall
------------

.. py:class:: brownie.network.contract.ContractCall(*args, block_identifier=None, override=None)

    Calls a non state-changing contract method without broadcasting a transaction, and returns the result. ``args`` must match the required inputs for the method.

    * ``args``: Input arguments for the call. The expected inputs are shown in the method's ``__repr__`` value.
    * ``block_identifier``: A block number or hash that the call is executed at. If ``None``, the latest block is used. Raises `ValueError` if this value is too far in the past and you are not using an archival node.
    *  ``override``: A mapping from addresses to balance, nonce, code, state, stateDiff overrides for the context of the call.

    Inputs and return values are formatted via methods in the :ref:`convert<api-convert>` module. Multiple values are returned inside a :func:`ReturnValue <brownie.convert.datatypes.ReturnValue>`.

    .. code-block:: python

        >>> Token[0].allowance
        <ContractCall object 'allowance(address,address)'>
        >>> Token[0].allowance(accounts[0], accounts[2])
        0

    For override see :ref:`ContractTx.call<override>` docs.

ContractCall Attributes
***********************

.. py:attribute:: ContractCall.abi

    The contract ABI specific to this method.

    .. code-block:: python

        >>> Token[0].allowance.abi
        {
            'constant': True,
            'inputs': [{'name': '_owner', 'type': 'address'}, {'name': '_spender', 'type': 'address'}],
            'name': "allowance",
            'outputs': [{'name': '', 'type': 'uint256'}],
            'payable': False,
            'stateMutability': "view",
            'type': "function"
        }

.. py:attribute:: ContractCall.signature

    The bytes4 signature of this method.

    .. code-block:: python

        >>> Token[0].allowance.signature
        '0xdd62ed3e'

ContractCall Methods
********************

.. py:classmethod:: ContractCall.info()

    Display `NatSpec documentation <https://solidity.readthedocs.io/en/latest/natspec-format.html>`_ documentation for the given method.

    .. code-block:: python

        >>> Token[0].allowance.info()
        allowance(address _owner, address _spender)
          @dev Function to check the amount of tokens than an owner
               allowed to a spender.
          @param _owner address The address which owns the funds.
          @param _spender address The address which will spend the funds.
          @return A uint specifying the amount of tokens still available
                  for the spender.

.. py:classmethod:: ContractCall.transact(*args)

    Sends a transaction to the method and returns a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>`.

    .. code-block:: python

        >>> tx = Token[0].allowance.transact(accounts[0], accounts[2])

        Transaction sent: 0xc4f3a0addfe1e475c2466f30c750ca7a60450132b07102af610d8d56f170046b
        Token.allowance confirmed - block: 2   gas used: 24972 (19.98%)
        <Transaction object '0xc4f3a0addfe1e475c2466f30c750ca7a60450132b07102af610d8d56f170046b'>
        >>> tx.return_value
        0

ContractTx
----------

.. py:class:: brownie.network.contract.ContractTx(*args)

    Broadcasts a transaction to a potentially state-changing contract method. Returns a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>`.

    The given ``args`` must match the required inputs for the method. The expected inputs are shown in the method's ``__repr__`` value.

    Inputs are formatted via methods in the :ref:`convert<api-convert>` module.

    You can optionally include a :py:class:`dict` of :ref:`transaction parameters<transaction-parameters>` as the final argument. If you omit this or do not specify a ``'from'`` value, the transaction will be sent from the same address that deployed the contract.

    .. code-block:: python

        >>> Token[0].transfer
        <ContractTx object 'transfer(address,uint256)'>
        >>> Token[0].transfer(accounts[1], 100000, {'from':accounts[0]})

        Transaction sent: 0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0
        Transaction confirmed - block: 2   gas spent: 51049
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>

ContractTx Attributes
*********************

.. py:attribute:: ContractTx.abi

    The contract ABI specific to this method.

    .. code-block:: python

        >>> Token[0].transfer.abi
        {
            'constant': False,
            'inputs': [{'name': '_to', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}],
            'name': "transfer",
            'outputs': [{'name': '', 'type': 'bool'}],
            'payable': False,
            'stateMutability': "nonpayable",
            'type': "function"
        }

.. py:attribute:: ContractTx.signature

    The bytes4 signature of this method.

    .. code-block:: python

        >>> Token[0].transfer.signature
        '0xa9059cbb'

ContractTx Methods
******************


.. py:classmethod:: ContractTx.call(*args, block_identifier=None, override=None)

    Calls the contract method without broadcasting a transaction, and returns the result.

    * ``args``: Input arguments for the call. The expected inputs are shown in the method's ``__repr__`` value.
    * ``block_identifier``: A block number or hash that the call is executed at. If ``None``, the latest block is used. Raises `ValueError` if this value is too far in the past and you are not using an archival node.
    * ``override``: A mapping from addresses to balance, nonce, code, state, stateDiff overrides for the context of the call.

    Inputs and return values are formatted via methods in the :ref:`convert<api-convert>` module. Multiple values are returned inside a :func:`ReturnValue <brownie.convert.datatypes.ReturnValue>`.

    .. code-block:: python

        >>> Token[0].transfer.call(accounts[2], 10000, {'from': accounts[0]})
        True

    .. _override:

    The override argument allows replacing balance, nonce and code associated with an address, as well as overwriting individual storage slot value.
    See `Geth docs <https://geth.ethereum.org/docs/rpc/ns-eth>`_ for more details.

    For example, you can query an exchange rate of an imbalanced Curve pool if it had a different A parameter:

    .. code-block:: python

        >>> for A in [300, 1000, 2000]:
                override = {
                    "0x5a6A4D54456819380173272A5E8E9B9904BdF41B": {
                        "stateDiff": {
                            "0x0000000000000000000000000000000000000000000000000000000000000009": hex(A * 100),
                        }
                    }
                }
                result = pool.get_dy_underlying(0, 1, 1e18, override=override)
                print(A, result.to("ether"))

        300 0.884657790783695579
        1000 0.961374099348799411
        2000 0.979998831913646748

.. py:classmethod:: ContractTx.decode_input(hexstr)

    Decodes hexstring input data for this method.

    .. code-block:: python

        >>>  Token[0].transfer.decode_input("0xa9059cbb0000000000000000000000000d36bdba474b5b442310a5bfb989903020249bba00000000000000000000000000000000000000000000000000000000000003e8")
        ("0xd36bdba474b5b442310a5bfb989903020249bba", 1000)

.. py:classmethod:: ContractTx.decode_output(hexstr)

    Decodes raw hexstring data returned by this method.

    .. code-block:: python

        >>>  Token[0].balanceOf.decode_output("0x00000000000000000000000000000000000000000000003635c9adc5dea00000")
        1000000000000000000000

.. py:classmethod:: ContractTx.encode_input(*args)

    Returns a hexstring of ABI calldata that can be used to call the method with the given arguments.

    .. code-block:: python

        >>> calldata = Token[0].transfer.encode_input(accounts[1], 1000)
        0xa9059cbb0000000000000000000000000d36bdba474b5b442310a5bfb989903020249bba00000000000000000000000000000000000000000000000000000000000003e8
        >>> accounts[0].transfer(Token[0], 0, data=calldata)

        Transaction sent: 0x8dbf15878104571669f9843c18afc40529305ddb842f94522094454dcde22186
        Token.transfer confirmed - block: 2   gas used: 50985 (100.00%)
        <Transaction object '0x8dbf15878104571669f9843c18afc40529305ddb842f94522094454dcde22186'>

.. py:classmethod:: ContractTx.info()

    Display `NatSpec documentation <https://solidity.readthedocs.io/en/latest/natspec-format.html>`_ documentation for the given method.

    .. code-block:: python

        >>> Token[0].transfer.info()
        transfer(address _to, uint256 _value)
          @dev transfer token for a specified address
          @param _to The address to transfer to.
          @param _value The amount to be transferred.

OverloadedMethod
----------------

.. py:class:: brownie.network.contract.OverloadedMethod(address, name, owner)

    When a contract uses `overloaded function names <https://solidity.readthedocs.io/en/latest/contracts.html#function-overloading>`_, the :func:`ContractTx <brownie.network.contract.ContractTx>` or :func:`ContractCall <brownie.network.contract.ContractCall>` objects are stored inside a :py:class:`dict`-like ``OverloadedMethod`` container.

    .. code-block:: python

        >>> erc223 = ERC223Token[0]
        >>> erc223.transfer
        <OverloadedMethod object 'ERC223Token.transfer'>

    Individual methods are mapped to keys that correspond to the function input types. Input types can be given as a single comma-seperated string or a tuple of strings. ``uint`` and ``uint256`` are equivalent.

    .. code-block:: python

        >>> erc223.transfer['address,uint']
        <ContractTx object 'transfer(address,uint256)'>

        >>> erc223.transfer['address', 'uint256', 'uint256']
        <ContractTx object 'transfer(address,uint256,uint256)'>

    When a contract only contains one method with the given name and number of arguements, ``OverloadedMethod`` may be called directly. When more than one method is present, a ``ValueError`` is raised.

    .. code-block:: python

        >>> erc223.transfer(accounts[0], "1 ether")
        Transaction sent: 0x8dbf15878104571669f9843c18afc40529305ddb842f94522094454dcde22186
        ERC223.transfer confirmed - block: 2   gas used: 50985 (100.00%)
        <Transaction object '0x8dbf15878104571669f9843c18afc40529305ddb842f94522094454dcde22186'>

InterfaceContainer
------------------

.. py:class:: brownie.network.contract.InterfaceContainer

    Container class that provides access to interfaces within a project.

    This object is created and populated with :func:`InterfaceConstructor <brownie.network.contract.InterfaceConstructor>` objects when a Brownie project is opened. It is available as ``interface`` within the console and as a pytest fixture.

    .. code-block:: python

        >>> interface
        <brownie.network.contract.InterfaceContainer object at 0x7fa239bf0d30>

InterfaceConstructor
--------------------

.. py:class:: brownie.network.contract.InterfaceConstructor(address, owner=None)

    Constructor to create :func:`Contract <brownie.network.contract.Contract>` objects from a project interface.

    * ``address_or_alias``: Address of the deployed contract.
    * ``owner``: An optional :func:`Account <brownie.network.account.Account>` instance. If given, transactions to the contract are sent broadcasted from this account by default.

    When a project is loaded, an ``InterfaceConstructor`` is generated from each interface file within the ``interfaces/`` folder of the project. These objects are stored as :func:`InterfaceContainer <brownie.network.contract.InterfaceContainer>` members.

    .. code-block:: python

        >>> interface.Dai
        <InterfaceConstructor 'Dai'>

        >>> interface.Dai("0x6B175474E89094C44Da98b954EedeAC495271d0F")
        <Dai Contract object '0x6B175474E89094C44Da98b954EedeAC495271d0F'>

InterfaceConstructor Attributes
*******************************

.. py:attribute:: InterfaceConstructor.abi

    The interface ABI as a :py:class:`dict`.

``brownie.network.event``
=========================

The ``event`` module contains classes and methods related to decoding transaction event logs. It is largely a wrapper around `eth-event <https://github.com/iamdefinitelyahuman/eth-event>`_.

Brownie stores encrypted event topics in ``brownie/data/topics.json``. The JSON file is loaded when this module is imported.

EventDict
---------

.. py:class:: brownie.network.event.EventDict

    Hybrid container type that works as a :py:class:`dict` and a :py:class:`list`. Base class, used to hold all events that are fired in a transaction.

    When accessing events inside the object:

    * If the key is given as an integer, events are handled as a list in the order that they fired. An :func:`_EventItem <brownie.network.event._EventItem>` is returned for the specific event that fired at the given position.
    * If the key is given as a string, an :func:`_EventItem <brownie.network.event._EventItem>` is returned that contains all the events with the given name.

    .. code-block:: python

        >>> tx
        <Transaction object '0xf1806643c21a69fcfa29187ea4d817fb82c880bcd7beee444ef34ea3b207cebe'>
        >>> tx.events
        {
            'CountryModified': [
                {
                    'country': 1,
                    'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                    'minrating': 1,
                    'permitted': True
                },
                    'country': 2,
                    'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                    'minrating': 1,
                    'permitted': True
                }
            ],
            'MultiSigCallApproved': {
                'callHash': "0x0013ae2e37373648c5161d81ca78d84e599f6207ad689693d6e5938c3ae4031d",
                'caller': "0xf9c1fd2f0452fa1c60b15f29ca3250dfcb1081b9"
            }
        }
        >>> tx.events['CountryModified']
        [
            {
                'country': 1,
                'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                'minrating': 1,
                'permitted': True
            },
                'country': 2,
                'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                'minrating': 1,
                'permitted': True
            }
        ]
        >>> tx.events[0]
        {
            'callHash': "0x0013ae2e37373648c5161d81ca78d84e599f6207ad689693d6e5938c3ae4031d",
            'caller': "0xf9c1fd2f0452fa1c60b15f29ca3250dfcb1081b9"
        }

.. py:classmethod:: EventDict.count(name)

    Returns the number of events that fired with the given name.

    .. code-block:: python

        >>> tx.events.count('CountryModified')
        2

.. py:classmethod:: EventDict.items

    Returns a set-like object providing a view on the object's items.

.. py:classmethod:: EventDict.keys

    Returns a set-like object providing a view on the object's keys.


.. py:classmethod:: EventDict.values

    Returns an object providing a view on the object's values.

EventWatcher
------------

.. py:class:: brownie.network.event.EventWatcher

    Singleton used to set callbacks on user-specified events.

    This class uses multiple threads:

        * The main thread (original process) starts a sub-thread and can be used to add callback instructions on events occurrences.
        * The sub-thread looks for new events among the ones with callback instructions.
        * When a new event is found, creates a new thread to run the callback instructions passing the event data as parameter.

.. py:classmethod:: EventWatcher.add_event_callback(event, callback, delay=2.0, repeat=True)

    Adds a callback instruction for the specified event.

    * ``event``: The ContractEvent instance to watch for.
    * ``callback``: The function to be called when a new ``event`` is detected. It MUST take one and only one parameter, which will be the event data.
    * ``delay``: The delay between each check for new ``event`` (s). Defaults to 2.
    * ``repeat``: Wether to repeat the callback or not (if ``False``, the callback instructions will only be called the first time events are detected). Defaults to ``True``.

    If the function is called with the same ``event`` more than once, the delay between each check for this ``event`` will take the minimum value between the already set delay and the one passed as parameter.

    This function raises a ``TypeError`` if the ``callback`` parameter is not a callable object.

.. py:classmethod:: EventWatcher.stop(wait=True)

    Sends the instruction to stop to the running threads.

    This function does not reset the instance to its initial state.

    If that is your goal, check the :func:`EventWatcher.reset <brownie.network.event.EventWatcher.reset>` method.

    * ``wait``: Wether to wait for threads to join within the function. Defaults to ``True``.

.. py:classmethod:: EventWatcher.reset

    Uses the :func:`EventWatcher.stop <brownie.network.event.EventWatcher.stop>` function to stop the running threads.

    After stopping, resets the instance to its default state.

Internal Classes and Methods
----------------------------

_EventItem
**********

.. py:class:: brownie.network.event._EventItem

    Hybrid container type that works as a :py:class:`dict` and a :py:class:`list`. Represents one or more events with the same name that were fired in a transaction.

    Instances of this class are created by :func:`EventDict <brownie.network.event.EventDict>`, it is not intended to be instantiated directly.

    When accessing events inside the object:

    * If the key is given as an integer, events are handled as a list in the order that they fired. An :func:`_EventItem <brownie.network.event._EventItem>` is returned for the specific event that fired at the given position.
    * If the key is given as a string, :func:`_EventItem <brownie.network.event._EventItem>` assumes that you wish to access the first event contained within the object. ``event['value']`` is equivalent to ``event[0]['value']``.

    All values within the object are formatted by methods outlined in the :ref:`convert<api-convert>` module.

    .. code-block:: python

        >>> event = tx.events['CountryModified']
        <Transaction object '0xf1806643c21a69fcfa29187ea4d817fb82c880bcd7beee444ef34ea3b207cebe'>
        >>> event
        [
            {
                'country': 1,
                'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                'minrating': 1,
                'permitted': True
            },
                'country': 2,
                'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                'minrating': 1,
                'permitted': True
            }
        ]
        >>> event[0]
        {
            'country': 1,
            'limits': (0, 0, 0, 0, 0, 0, 0, 0),
            'minrating': 1,
            'permitted': True
        }
        >>> event['country']
        1
        >>> event[1]['country']
        2

.. py:attribute:: _EventItem.name

    The name of the event(s) contained within this object.

    .. code-block:: python

        >>> tx.events[2].name
        CountryModified

.. py:attribute:: _EventItem.address

    The address where the event was fired. If the object contains multiple events, this value is set to ``None``.

    .. code-block:: python

        >>> tx.events[2].address
        "0x2d72c1598537bcf4a4af97668b3a24e68b7d0cc5"

.. py:attribute:: _EventItem.pos

    A tuple giving the absolute position of each event contained within this object.

    .. code-block:: python

        >>> event.pos
        (1, 2)
        >>> event[1].pos
        (2,)
        >>> tx.events[2] == event[1]
        True

.. py:classmethod:: _EventItem.items

    Returns a set-like object providing a view on the items in the first event within this object.

.. py:classmethod:: _EventItem.keys

    Returns a set-like object providing a view on the keys in the first event within this object.

.. py:classmethod:: _EventItem.values

    Returns an object providing a view on the values in the first event within this object.

Internal Methods
****************

.. py:method:: brownie.network.event._get_topics(abi)

    Generates encoded topics from the given ABI, merges them with those already known in ``topics.json``, and returns a dictioary in the form of ``{'Name': "encoded topic hexstring"}``.

    .. code-block:: python

        >>> from brownie.network.event import _get_topics
        >>> abi = [{'name': 'Approval', 'anonymous': False, 'type': 'event', 'inputs': [{'name': 'owner', 'type': 'address', 'indexed': True}, {'name': 'spender', 'type': 'address', 'indexed': True}, {'name': 'value', 'type': 'uint256', 'indexed': False}]}, {'name': 'Transfer', 'anonymous': False, 'type': 'event', 'inputs': [{'name': 'from', 'type': 'address', 'indexed': True}, {'name': 'to', 'type': 'address', 'indexed': True}, {'name': 'value', 'type': 'uint256', 'indexed': False}]}]
        >>> _get_topics(abi)
        {'Transfer': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', 'Approval': '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925'}


.. py:method:: brownie.network.event._decode_logs(logs)

    Given an array of logs as returned by ``eth_getLogs`` or ``eth_getTransactionReceipt`` RPC calls, returns an :func:`EventDict <brownie.network.event.EventDict>`.

    .. code-block:: python

        >>> from brownie.network.event import _decode_logs
        >>> tx = Token[0].transfer(accounts[1], 100)

        Transaction sent: 0xfefc3b7d912ed438b312414fb31d94ff757970f4d2e74dd0950d5c58cc23fdb1
        Token.transfer confirmed - block: 2   gas used: 50993 (33.77%)
        <Transaction object '0xfefc3b7d912ed438b312414fb31d94ff757970f4d2e74dd0950d5c58cc23fdb1'>
        >>> e = _decode_logs(tx.logs)
        >>> repr(e)
        <brownie.types.types.EventDict object at 0x7feed74aebe0>
        >>> e
        {
            'Transfer': {
                'from': "0x1ce57af3672a16b1d919aeb095130ab288ca7456",
                'to': "0x2d72c1598537bcf4a4af97668b3a24e68b7d0cc5",
                'value': 100
            }
        }

.. py:method:: brownie.network.event._decode_trace(trace)

    Given the ``structLog`` from a ``debug_traceTransaction`` RPC call, returns an :func:`EventDict <brownie.network.event.EventDict>`.

    .. code-block:: python

        >>> from brownie.network.event import _decode_trace
        >>> tx = Token[0].transfer(accounts[2], 1000, {'from': accounts[3]})

        Transaction sent: 0xc6365b065492ea69ad3cbe26039a45a68b2e9ab9d29c2ff7d5d9162970b176cd
        Token.transfer confirmed (Insufficient Balance) - block: 2   gas used: 23602 (19.10%)
        <Transaction object '0xc6365b065492ea69ad3cbe26039a45a68b2e9ab9d29c2ff7d5d9162970b176cd'>
        >>> e = _decode_trace(tx.trace)
        >>> repr(e)
        <brownie.types.types.EventDict object at 0x7feed74aebe0>
        >>> e
        {}


``brownie.network.gas``
=======================

The ``gas`` module contains gas strategy classes, as well as abstract base classes for building your own gas strategies.

Gas Strategies
--------------

.. py:class:: brownie.network.gas.strategies.ExponentialScalingStrategy(initial_gas_price, max_gas_price, time_duration=30)

    Time based scaling strategy for exponential gas price increase.

    The gas price for each subsequent transaction is calculated as the previous price multiplied by `1.1 ** n` where n is the number of transactions that have been broadcast. In this way the price increase starts gradually and ramps up until confirmation.

    * ``initial_gas_price``: The initial gas price to use in the first transaction
    * ``max_gas_price``: The maximum gas price to use
    * ``time_duration``: Number of seconds between transactions

    .. code-block:: python

        >>> from brownie.network.gas.strategies import ExponentialScalingStrategy
        >>> gas_strategy = ExponentialScalingStrategy("10 gwei", "50 gwei")

        >>> accounts[0].transfer(accounts[1], "1 ether", gas_price=gas_strategy)

.. py:class:: brownie.network.gas.strategies.GasNowStrategy(speed="fast")

    Gas strategy for determing a price using the `GasNow <https://www.gasnow.org/>`_ API.

    * ``speed``: The gas price to use based on the API call. Options are rapid, fast, standard and slow.

    .. code-block:: python

        >>> from brownie.network.gas.strategies import GasNowStrategy
        >>> gas_strategy = GasNowStrategy("fast")

        >>> accounts[0].transfer(accounts[1], "1 ether", gas_price=gas_strategy)

.. py:class:: brownie.network.gas.strategies.GasNowScalingStrategy(initial_speed="standard", max_speed="rapid", increment=1.125, block_duration=2)

    Block based scaling gas strategy using the GasNow API.

    * ``initial_speed``: The initial gas price to use when broadcasting the first transaction. Options are rapid, fast, standard and slow.
    * ``max_speed``: The maximum gas price to use when replacing the transaction. Options are rapid, fast, standard and slow.
    * ``increment``: A multiplier applied to the most recently used gas price in order to determine the new gas price. If the incremented value is less than or equal to the current ``max_speed`` rate, a new transaction is broadcasted. If the current rate for ``initial_speed`` is greater than the incremented rate, it is used instead.
    * ``block_duration``: The number of blocks to wait between broadcasting new transactions.

    .. code-block:: python

        >>> from brownie.network.gas.strategies import GasNowScalingStrategy
        >>> gas_strategy = GasNowScalingStrategy("standard", increment=1.125, block_duration=2)

        >>> accounts[0].transfer(accounts[1], "1 ether", gas_price=gas_strategy)

.. py:class:: brownie.network.gas.strategies.GethMempoolStrategy(position=500, graphql_endpoint=None, block_duration=2)

    Block based scaling gas strategy using Geth's `GraphQL interface <https://eips.ethereum.org/EIPS/eip-1767>`_.

    In order to use this strategy you must be connecting via a Geth node with GraphQL enabled.

    The yielded gas price is determined by sorting transactions in the mempool according to gas price, and returning the price of the transaction at `position`. This is the same technique used by the GasNow API.

    * A position of 200 or less usually places a transaction within the mining block.
    * A position of 500 usually places a transaction within the 2nd pending block.

    .. code-block:: python

        >>> from brownie.network.gas.strategies import GethMempoolStrategy
        >>> gas_strategy = GethMempoolStrategy(200)

        >>> accounts[0].transfer(accounts[1], "1 ether", gas_price=gas_strategy)

.. py:class:: brownie.network.gas.strategies.LinearScalingStrategy(initial_gas_price, max_gas_price, increment=1.125, time_duration=30)

    Time based scaling strategy for linear gas price increase.

    * ``initial_gas_price``: The initial gas price to use in the first transaction
    * ``max_gas_price``: The maximum gas price to use
    * ``increment``: Multiplier applied to the previous gas price in order to determine the new gas price
    * ``time_duration``: Number of seconds between transactions

    .. code-block:: python

        >>> from brownie.network.gas.strategies import LinearScalingStrategy
        >>> gas_strategy = LinearScalingStrategy("10 gwei", "50 gwei", 1.1)

        >>> accounts[0].transfer(accounts[1], "1 ether", gas_price=gas_strategy)

.. _api-network-gas-abc:

Gas Strategy ABCs
-----------------

`Abstract base classes <https://docs.python.org/3/library/abc.html#module-abc>`_ for building your own gas strategies.

Simple Strategies
*****************

.. py:class:: brownie.network.gas.bases.SimpleGasStrategy

    Abstract base class for simple gas strategies.

    Simple gas strategies are called once to provide a dynamically genreated gas price at the time a transaction is broadcasted. Transactions using simple gas strategies are not automatically rebroadcasted.

Simple Strategy Abstract Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To implement a simple gas strategy, subclass :func:`SimpleGasStrategy <brownie.network.gas.bases.SimpleGasStrategy>` and include the following method:

.. py:method:: SimpleGasStrategy.get_gas_price(self) -> int:

    Return the gas price for a transaction.

Scaling Strategies
******************

.. py:class:: brownie.network.gas.bases.BlockGasStrategy(duration=2)

    Abstract base class for block-based gas strategies.

    Block gas strategies are called every ``duration`` blocks and can be used to automatically rebroadcast a pending transaction with a higher gas price.

.. py:class:: brownie.network.gas.bases.TimeGasStrategy(duration=30)

    Abstract base class for time-based gas strategies.

    Time gas strategies are called every ``duration`` seconds and can be used to automatically rebroadcast a pending transaction with a higher gas price.

Scaling Strategy Abstract Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To implement a scaling strategy, subclass one of the above ABCs and implement the following generator function:

.. py:method:: BlockGasStrategy.get_gas_price(self) -> Generator[int]:

    Generator function that yields a new gas price each time it is called.

    The produced generator is called every ``duration`` seconds while a transaction is still pending. Each call must yield a new gas price as an integer. If the newly yielded value is at least 10% higher than the current gas price, the transaction is rebroadcasted with the new gas price.

``brownie.network.multicall``
=============================

The ``multicall`` module contains the :func:`Multicall <brownie.network.multicall.Multicall>` context manager, which allows for the batching of multiple constant contract function calls via ``Multicall2``.

.. note::

    The :func:`Multicall <brownie.network.multicall.Multicall>` context manager is not meant to be instantiated, and instead should be used via ``brownie.multicall``

Multicall
---------

.. py:class:: brownie.network.multicall.Multicall(address=None, block_identifier=None)

    Instances of ``Multicall`` allow for the batching of constant contract function calls through a modified version of the standard Brownie call API.

    The only syntatic difference between a multicall and a standard brownie contract function call is the final argument for a multicall, is a dictionary with the ``from`` key being the instance of ``Multicall`` being used.

    Features:

        1. Lazy fetching of results
        2. Auto-deployment on development networks (on first use).
        3. Uses ``multicall2`` key in network-config as pre-defined multicall contract address
        4. Can specify/modify block number to make calls at particular block heights
        5. Calls which fail return ``None`` instead of causing all calls to fail

    .. code-block:: python

        >>> import brownie
        >>> from brownie import Contract
        >>> addr_provider = Contract("0x0000000022D53366457F9d5E68Ec105046FC4383")
        >>> registry = Contract(addr_provider.get_registry())
        >>> with brownie.multicall:
        ...     pool_count = registry.pool_count.call()  # standard call, no batching
        ...     pools = [registry.pool_list(i) for i in range(pool_count)]  # batched
        ...     gauges = [registry.get_gauges(pool) for pool in pools]  # batched
        ... print(*zip(pools, gauges), sep="\n")

Multicall Attributes
********************

.. py:attribute:: Multicall.address

    The deployed ``Multicall2`` contract address used for batching calls.

    .. code-block:: python

        >>> brownie.multicall.address
        0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696
        >>> brownie.multicall(address="0xc8E51042792d7405184DfCa245F2d27B94D013b6").address
        0xc8E51042792d7405184DfCa245F2d27B94D013b6

.. py:attribute:: Multicall.block_number

    The block height which call results are aggregated from.

    .. note::

        ``Multicall`` relies on an instance of ``Multicall2`` being available for aggregating results. If you set the block_height before the ``Multicall2`` instance you are using was deployed a ``ContractNotFound`` error will be raised.

    .. code-block:: python

        >>> with brownie.multicall(block_identifier=12733683):
        ...     brownie.multicall.block_number
        12733683

.. py:attribute:: Multicall.default_verbose

    Default verbosity setting for multicall. Set to ``False`` by default. If set to ``True``, the content of each batched call is printed to the console. This is useful for debugging, to ensure a multicall is performing as expected.

    .. code-block:: python

        >>> multicall.default_verbose = True

    You can also enable verbosity for individual multicalls by setting the `verbose` keyword:

    .. code-block:: python

        >>> with brownie.multicall(verbose=True):
        ...

Multicall Methods
*****************

.. py:classmethod:: Multicall.deploy

    Deploys an instance of ``Multicall2``, especially useful when creating fixtures for testing.

    .. code-block:: python

        >>> multicall2 = brownie.multicall.deploy({"from": alice})
        <Multicall2 Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

.. py:classmethod:: Multicall.flush

    Flushes the current queue of pending calls, especially useful for preventing ``OOG`` errors from occuring when querying large amounts of data.

    >>> results = []
    >>> long_list_of_addresses = [...]
    >>> token = Contract(...)
    >>> with brownie.multicall:
    ...     for i, addr in enumerate(long_list_of_addresses):
    ...         if i % 1_000:
    ...             brownie.multicall.flush()
    ...         results.append(token.balanceOf(addr))

Multicall Internal Attributes
*****************************

.. py:attribute:: Multicall._contract

    The contract instance of ``Multicall2`` used to query data

.. py:attribute:: Multicall._pending_calls

    List of proxy objects representing calls to be made. While pending, these calls contain the data necessary to make an aggregate call with multicall and also decode the result.



``brownie.network.state``
=========================

The ``state`` module contains classes to record transactions and contracts as they occur on the blockchain.

Classes in ``state`` are not meant to be instantiated directly. :func:`TxHistory <brownie.network.state.TxHistory>` and :func:`Chain <brownie.network.state.Chain>` objects are available as ``history`` and ``chain`` in the console and as pytest fixtures.

TxHistory
---------

.. py:class:: brownie.network.state.TxHistory

    List-like :func:`Singleton <brownie._singleton._Singleton>` container that contains :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` objects. Whenever a transaction is broadcast, the :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` is automatically added.

    .. code-block:: python

        >>> from brownie.network.state import TxHistory
        >>> history = TxHistory()
        >>> history
        []
        >>> dir(history)
        [copy, from_sender, of_address, to_receiver]

TxHistory Attributes
********************

.. py:attribute:: TxHistory.gas_profile

    A :py:class:`dict` that tracks gas cost statistics for contract function calls over time.

    .. code-block:: python

        >>> history.gas_profile
        {
            'Token.constructor': {
                'avg': 742912,
                'count': 1,
                'high': 742912,
                'low': 742912
            },
            'Token.transfer': {
                'avg': 43535,
                'count': 2,
                'high': 51035,
                'low': 36035
            }
        }

TxHistory Methods
*****************

.. py:classmethod:: TxHistory.copy

    Returns a shallow copy of the object as a :py:class:`list`.

    .. code-block:: python

        >>> history
        [<Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>]
        >>> c = history.copy()
        >>> c
        [<Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>]
        >>> type(c)
        <class 'list'>

.. py:classmethod:: TxHistory.filter(key=None, **kwargs)

    Return a filtered list of transactions.

    Each keyword argument corresponds to a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` attribute. Only transactions where every attributes matches the given value are returned.

    .. code-block:: python

        >>> history.filter(sender=accounts[0], value="1 ether")
        [<Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>]

    You can also use ``key`` to provide a function or lambda. It should receive one argument, a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>`, and return a boolean indicating if the object is to be included in the result.

    .. code-block:: python

        >>> history.filter(key=lambda k: k.nonce < 2)
        [<Transaction '0x03569ee152b04ba5b55c2bf05f99f7ec153db715acfe0c1600f144ded58f31fe'>, <Transaction '0x42193c0ff7007c6e2a5e5572a3c6b5706cd133d21e30e5826add3d971134504c'>]

.. py:classmethod:: TxHistory.from_sender(account)

    Returns a list of transactions where the sender is :func:`Account <brownie.network.account.Account>`.

    .. code-block:: python

        >>> history.from_sender(accounts[1])
        [<Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>]

.. py:classmethod:: TxHistory.to_receiver(account)

    Returns a list of transactions where the receiver is :func:`Account <brownie.network.account.Account>`.

    .. code-block:: python

        >>> history.to_receiver(accounts[2])
        [<Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>]

.. py:classmethod:: TxHistory.of_address(account)

    Returns a list of transactions where :func:`Account <brownie.network.account.Account>` is the sender or receiver.

    .. code-block:: python

        >>> history.of_address(accounts[1])
        [<Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>]

.. py:classmethod:: TxHistory.wait(key=None, **kwargs)

    Wait for pending transactions to confirm.

    This method iterates over a list of transactions generated by :func:`TxHistory.filter <TxHistory.filter>`, waiting until each transaction has confirmed. If no arguments are given, all transactions within the container are used.

TxHistory Internal Methods
**************************

.. py:classmethod:: TxHistory._reset()

    Called by :func:`state._notify_registry <brownie.network.state._notify_registry>` when the local chain has been reset. All :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` objects are removed from the container.

.. py:classmethod:: TxHistory._revert(height)

    Called by :func:`state._notify_registry <brownie.network.state._notify_registry>` when the local chain has been reverted to a block height greater than zero. Any :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` objects that no longer exist are removed from the container.

Chain
-----

.. py:class:: brownie.network.state.Chain

    List-like :func:`Singleton <brownie._singleton._Singleton>` used to access chain information and perform actions such as snapshotting, rewinds and time travel.

    .. code-block:: python

        >>> from brownie.network.state import Chain
        >>> chain = Chain()
        >>> chain
        <Chain object (chainid=1, height=10451202)>

    You can use list indexing the access specific blocks. For negative index values, the block returned is relative to the most recently mined block. For example, ``chain[-1]`` returns the most recently mined block.

    .. code-block:: python

        >>> web3.eth.block_number
        10451202

        >>> len(chain)
        10451203  # always +1 to the current block number, because the first block is zero

        >>> chain[0] == web3.eth.get_block(0)
        True

        >>> chain[-1] == web3.eth.get_block('latest')
        True

Chain Attributes
****************

.. py:attribute:: Chain.height

    The current block height.

    .. code-block:: python

        >>> chain.height
        10451202

.. py:attribute:: Chain.id

    The chain ID value for the active network. Returns ``None`` if no chain ID is available.

    .. code-block:: python

        >>> chain.id
        1

Chain Methods
*************

.. py:method:: Chain.get_transaction(txid)

    Return a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` object for the given transaction hash.

    This function is non-blocking. Pending transaction return immediately.

    Raises ``TransactionNotFound`` if the transaction does not exist.

    .. code-block:: python

        >>> chain.get_transaction(0xf598d43ef34a48478f3bb0ad969c6735f416902c4eb1eb18ebebe0fca786105e)
        <Transaction '0xf598d43ef34a48478f3bb0ad969c6735f416902c4eb1eb18ebebe0fca786105e'>

.. py:method:: Chain.new_blocks(height_buffer, poll_interval)

    Generator for iterating over new blocks.

    ``height_buffer``: The number of blocks behind "latest" to return. A higher value means more delayed results but less likelihood of uncles.
    ``poll_interval``: Maximum interval between querying for a new block, if the height has not changed. Set this lower to detect uncles more frequently.

    .. code-block:: python

        count = 0
        for block in chain.new_blocks():
            print(block.number)
            count += 1
            if count == 5:
                break

.. py:method:: Chain.time()

    Return the current epoch time in the RPC as an integer.

    .. code-block:: python

        >>> chain.time()
        1550189043

.. py:method:: Chain.sleep(seconds)

    Advance the RPC time. You can only advance the time by whole seconds.

    .. code-block:: python

        >>> chain.time()
        1550189043
        >>> chain.sleep(100)
        >>> chain.time()
        1550189143

.. py:method:: Chain.mine(blocks=1, timestamp=None, timedelta=None)

    Mine one or more empty blocks.

    * ``blocks``: Number of blocks to mine
    * ``timestamp``: Timestamp of the final block being mined. If multiple blocks are mined, they will be mined at equal intervals starting from :func:`chain.time <Chain.time>` and ending at ``timestamp``.
    * ``timedelta``: Timedelta for the final block to be mined. If given, the final block will have a timestamp of ``chain.time() + timedelta``.

    Returns the block height after all new blocks have been mined.

    .. code-block:: python

        >>> web3.eth.block_number
        0
        >>> chain.mine()
        1
        >>> chain.mine(3)
        4

.. py:method:: Chain.snapshot()

    Create a snapshot at the current block height.

    .. code-block:: python

        >>> chain.snapshot()

.. py:method:: Chain.revert()

    Revert the blockchain to the latest snapshot. Raises ``ValueError`` if no snapshot has been taken.

    .. code-block:: python

        >>> chain.snapshot()
        >>> accounts[0].balance()
        100000000000000000000
        >>> accounts[0].transfer(accounts[1], "10 ether")

        Transaction sent: 0xd5d3b40eb298dfc48721807935eda48d03916a3f48b51f20bcded372113e1dca
        Transaction confirmed - block: 5   gas used: 21000 (100.00%)
        <Transaction object '0xd5d3b40eb298dfc48721807935eda48d03916a3f48b51f20bcded372113e1dca'>
        >>> accounts[0].balance()
        89999580000000000000
        >>> chain.revert()
        4
        >>> accounts[0].balance()
        100000000000000000000

.. py:method:: Chain.reset()

    Reset the local environment to the initial state when Brownie was loaded. This action is performed using a snapshot - it is NOT equivalent to calling :func:`rpc.kill <Rpc.kill>` and then :func:`rpc.launch <Rpc.launch>`.

    Returns the block height after resetting.

    .. code-block:: python

        >>> chain.reset()
        0

.. py:method:: Chain.undo(num=1)

    Undo one or more recent transactions.

    * ``num``: Number of transactions to undo

    Once undone, a transaction can be repeated using :func:`Chain.redo <Chain.redo>`. Calling :func:`Chain.snapshot <Chain.snapshot>` or :func:`Chain.revert <Chain.revert>` clears the undo buffer.

    Returns the block height after all undo actions are complete.

    .. code-block:: python

        >>> web3.eth.block_number
        3
        >>> chain.undo()
        2

.. py:method:: Chain.redo(num=1)

    Redo one or more recently undone transactions.

    * ``num``: Number of transactions to redo

    Returns the block height after all redo actions are complete.

    .. code-block:: python

        >>> web3.eth.block_number
        2
        >>> chain.redo()
        Transaction sent: 0x8c166b66b356ad7f5c58337973b89950f03105cdae896ac66f16cdd4fc395d05
          Gas price: 0.0 gwei   Gas limit: 6721975
          Transaction confirmed - Block: 3   Gas used: 21000 (0.31%)

        3

Internal Methods
----------------

The internal methods in the ``state`` module are used for tracking and adjusting the contents of various container objects when the local RPC network is reverted or reset.

.. py:function:: brownie.network.state._revert_register(obj)

    Registers an object to be called whenever the local RPC is reset or reverted. Objects that register must include ``_revert`` and ``_reset`` methods in order to receive these callbacks.

.. py:function:: brownie.network.state._notify_registry(height)

    Calls each registered object's ``_revert`` or ``_reset`` method after the local state has been reverted.


.. py:function:: brownie.network.state._add_contract(contract)

    Adds a :func:`Contract <brownie.network.contract.Contract>` or :func:`ProjectContract <brownie.network.contract.ProjectContract>` object to the global contract record.

.. py:function:: brownie.network.state._find_contract(address)

    Given an address, returns the related :func:`Contract <brownie.network.contract.Contract>` or :func:`ProjectContract <brownie.network.contract.ProjectContract>` object. If none exists, returns ``None``.

    This function is used internally by Brownie to locate a :func:`ProjectContract <brownie.network.contract.ProjectContract>` when the project it belongs to is unknown.

.. py:function:: brownie.network.state._remove_contract(contract)

    Removes a :func:`Contract <brownie.network.contract.Contract>` or :func:`ProjectContract <brownie.network.contract.ProjectContract>` object to the global contract record.

.. py:function:: brownie.network.state._get_current_dependencies()

    Returns a list of the names of all currently deployed contracts, and of every contract that these contracts are dependent upon.

    Used during testing to determine which contracts must change before a test needs to be re-run.

``brownie.network.rpc``
=======================

The ``rpc`` module contains the :func:`Rpc <brownie.network.rpc.Rpc>` class, which is used to interact with ``ganache-cli`` when running a local RPC environment.

.. note:: Account balances, contract containers and transaction history are automatically modified when the local RPC is terminated, reset or reverted.

Rpc
---

.. py:class:: brownie.network.rpc.Rpc

    :func:`Singleton <brownie._singleton._Singleton>` object for interacting with ``ganache-cli`` when running a local RPC environment. When using the console or writing tests, an instance of this class is available as ``rpc``.

    .. code-block:: python

        >>> from brownie import rpc
        >>> rpc
        <lib.components.eth.Rpc object at 0x7ffb7cbab048>
        >>> dir(rpc)
        [is_active, kill, launch, mine, reset, revert, sleep, snapshot, time]

Rpc Methods
***********

.. py:classmethod:: Rpc.launch(cmd)

    Launches the local RPC client as a `subprocess <https://docs.python.org/3/library/subprocess.html#subprocess.Popen>`_. ``cmd`` is the command string requiried to run it.

    If the process cannot load successfully, raises ``brownie.RPCProcessError``.

    If a provider has been set in :func:`Web3 <brownie.network.web3.Web3>` but is unable to connect after launching, raises :func:`RPCConnectionError <brownie.exceptions.RPCConnectionError>`.

    .. code-block:: python

        >>> rpc.launch('ganache-cli')
        Launching 'ganache-cli'...

.. py:classmethod:: Rpc.attach(laddr)

    Attaches to an already running RPC client.

    ``laddr``: Address that the client is listening at. Can be supplied as a string ``"http://127.0.0.1:8545"`` or tuple ``("127.0.0.1", 8545)``.

    Raises a ``ProcessLookupError`` if the process cannot be found.

    .. code-block:: python

        >>> rpc.attach('http://127.0.0.1:8545')

.. py:classmethod:: Rpc.kill(exc=True)

    Kills the RPC subprocess. Raises ``SystemError`` if ``exc`` is ``True`` and the RPC is not currently active.

    .. code-block:: python

        >>> rpc.kill()
        Terminating local RPC client...

    .. note:: Brownie registers this method with the `atexit <https://docs.python.org/3/library/atexit.html>`_ module. It is not necessary to explicitly kill :func:`Rpc <brownie.network.rpc.Rpc>` before terminating a script or console session.

.. py:classmethod:: Rpc.is_active()

    Returns a boolean indicating if the RPC process is currently active.

    .. code-block:: python

        >>> rpc.is_active()
        False
        >>> rpc.launch()
        >>> rpc.is_active()
        True

.. py:classmethod:: Rpc.is_child()

    Returns a boolean indicating if the RPC process is a child process of Brownie. If the RPC is not currently active, returns ``False``.

    .. code-block:: python

        >>> rpc.is_child()
        True

.. py:classmethod:: Rpc.evm_version()

    Returns the currently active EVM version as a string.

    .. code-block:: python

        >>> rpc.evm_version()
        'istanbul'

.. py:classmethod:: Rpc.evm_compatible(version)

    Returns a boolean indicating if the given ``version`` is compatible with the currently active EVM version.

    .. code-block:: python

        >>> rpc.evm_compatible('byzantium')
        True

``brownie.network.transaction``
===============================

The ``transaction`` module contains the :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` class and related internal methods.

TransactionReceipt
------------------

.. py:class:: brownie.network.transaction.TransactionReceipt

    An instance of this class is returned whenever a transaction is broadcasted. When printed in the console, the transaction hash will appear yellow if the transaction is still pending or red if the transaction caused the EVM to revert.

    Many of the attributes return ``None`` while the transaction is still pending.

    .. code-block:: python

        >>> tx = Token[0].transfer
        <ContractTx object 'transfer(address,uint256)'>
        >>> Token[0].transfer(accounts[1], 100000, {'from':accounts[0]})

        Transaction sent: 0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0
        Transaction confirmed - block: 2   gas spent: 51049
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> dir(tx)
        [block_number, call_trace, contract_address, contract_name, error, events, fn_name, gas_limit, gas_price, gas_used, info, input, logs, nonce, receiver, sender, status, txid, txindex, value]

TransactionReceipt Attributes
*****************************

.. py:attribute:: TransactionReceipt.block_number

    The block height at which the transaction confirmed.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.block_number
        2

.. py:attribute:: TransactionReceipt.confirmations

    The number of blocks mined since the transaction was confirmed, including the block the transaction was mined in: ``block_height - tx.block_number + 1``.

    .. code-block:: python

        >>> tx
        <Transaction '0x8c166b66b356ad7f5c58337973b89950f03105cdae896ac66f16cdd4fc395d05'>
        >>> tx.confirmations
        11

.. py:attribute:: TransactionReceipt.contract_address

    The address of the contract deployed in this transaction, if the transaction was a deployment.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.contract_address
        None

    For contracts deployed as the result of calling another contract, see :func:`TransactionReceipt.new_contracts <TransactionReceipt.new_contracts>`.

.. py:attribute:: TransactionReceipt.contract_name

    The name of the contract that was called or deployed in this transaction.

    .. code-block:: python

        >>> tx
        <Transaction object '0xcdd07c6235bf093e1f30ac393d844550362ebb9b314b7029667538bfaf849749'>
        >>> tx.contract_name
        Token


.. py:attribute:: TransactionReceipt.dev_revert_msg

    The :ref:`developer revert comment<dev-revert>` returned when a transaction causes the EVM to revert, if any.

    .. code-block:: python

        >>> tx
        <Transaction object '0xd9e0fb1bd6532f6aec972fc8aef806a8d8b894349cf5c82c487335625db8d0ef'>
        >>> tx.dev_revert_msg
        'dev: is four'

.. py:attribute:: TransactionReceipt.events

    An :func:`EventDict <brownie.network.event.EventDict>` of decoded event logs for this transaction.

    .. note:: If you are connected to an RPC client that allows for ``debug_traceTransaction``, event data is still available when the transaction reverts.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.events
        {
            'Transfer': {
                'from': "0x94dd96c7e6012c927537cd789c48c42a1d1f790d",
                'to': "0xc45272e89a23d1a15a24041bce7bc295e79f2d13",
                'value': 100000
            }
        }

.. py:attribute:: TransactionReceipt.fn_name

    The name of the function called by the transaction.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.fn_name
        'transfer'

.. py:attribute:: TransactionReceipt.gas_limit

    The gas limit of the transaction, in wei as an ``int``.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.gas_limit
        150921

.. py:attribute:: TransactionReceipt.gas_price

    The effective gas price of the transaction, in wei as an ``int``.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.gas_price
        2000000000

.. py:attribute:: TransactionReceipt.gas_used

    The amount of gas consumed by the transaction, in wei as an ``int``.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.gas_used
        51049

.. py:attribute:: TransactionReceipt.input

    The complete calldata of the transaction as a hexstring.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.input
        '0xa9059cbb00000000000000000000000031d504908351d2d87f3d6111f491f0b52757b592000000000000000000000000000000000000000000000000000000000000000a'

.. py:attribute:: TransactionReceipt.internal_transfers

    A list of all internal ether transfers that occurred during the transaction. Transfers are sequenced in the order they took place, and represented as dictionaries containing the following fields:

    * ``from``: Sender address
    * ``to``: Receiver address
    * ``value``: Amount of ether that was transferred in :func:`Wei <brownie.convert.datatypes.Wei>`

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.internal_transfers
        [
            {
                "from": "0x79447c97b6543F6eFBC91613C655977806CB18b0",
                "to": "0x21b42413bA931038f35e7A5224FaDb065d297Ba3",
                "value": 100
            }
        ]

.. py:attribute:: TransactionReceipt.logs

    The raw event logs for the transaction. Not available if the transaction reverts.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.logs
        [AttributeDict({'logIndex': 0, 'transactionIndex': 0, 'transactionHash': HexBytes('0xa8afb59a850adff32548c65041ec253eb64e1154042b2e01e2cd8cddb02eb94f'), 'blockHash': HexBytes('0x0b93b4cf230c9ef92b990de9cd62611447d83d396f1b13204d26d28bd949543a'), 'blockNumber': 6, 'address': '0x79447c97b6543F6eFBC91613C655977806CB18b0', 'data': '0x0000000000000000000000006b5132740b834674c3277aafa2c27898cbe740f600000000000000000000000031d504908351d2d87f3d6111f491f0b52757b592000000000000000000000000000000000000000000000000000000000000000a', 'topics': [HexBytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef')], 'type': 'mined'})]

.. py:attribute:: TransactionReceipt.modified_state

    Boolean indicating if this transaction resuled in any state changes on the blockchain.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.modified_state
        True

.. py:attribute:: TransactionReceipt.new_contracts

    A list of new contract addresses that were deployed during this transaction, as the result of contract call.

    .. code-block:: python

        >>> tx = Deployer.deploy_new_contract()
        Transaction sent: 0x6c3183e41670101c4ab5d732bfe385844815f67ae26d251c3bd175a28604da92
          Gas price: 0.0 gwei   Gas limit: 79781
          Deployer.deploy_new_contract confirmed - Block: 4   Gas used: 79489 (99.63%)

        >>> tx.new_contracts
        ["0x1262567B3e2e03f918875370636dE250f01C528c"]


.. py:attribute:: TransactionReceipt.nonce

    The nonce of the transaction.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.nonce
        2

.. py:attribute:: TransactionReceipt.receiver

    The address the transaction was sent to, as a string.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.receiver
        '0x79447c97b6543F6eFBC91613C655977806CB18b0'

.. py:attribute:: TransactionReceipt.revert_msg

    The error string returned when a transaction causes the EVM to revert, if any.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.revert_msg
        None

.. py:attribute:: TransactionReceipt.return_value

    The value returned from the called function, if any. Only available if the RPC client allows ``debug_traceTransaction``.

    If more then one value is returned, they are stored in a :func:`ReturnValue <brownie.convert.datatypes.ReturnValue>`.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.return_value
        True

.. py:attribute:: TransactionReceipt.subcalls

    A list of dictionaries providing information about subcalls that occured during the transaction.

    The following fields are always included:

    * ``from``: Address where the call originated
    * ``to``: Address being called
    * ``op``: Instruction used to make the call

    The following fields are included when the source code for ``to`` is known:

    * ``function``: Signature of the function being called
    * ``inputs``: Dictionary of decoded input arguments in the call

    One of the following fields is included, depending on how the call ends:

    * ``return_value``: A tuple of decoded return values, if the call ended with ``RETURN``
    * ``revert_msg``: The given error message, if the call ended in a ``REVERT`` or ``INVALID`` instruction
    * ``selfdestruct``: Set to ``True`` if the call ended in a ``SELFDESTRUCT`` instruction

    .. code-block:: python

        >>> history[-1].subcalls
        [
            {
                'from': "0x5AE569698C5F986665018B6e1d92A71be71DEF9a",
                'function': "get_period_timestamp(int128)",
                'inputs': {
                    'p': 0
                },
                'op': "STATICCALL",
                'return_value': (1594574319,),
                'to': "0x0C41Fc429cC21BC3c826efB3963929AEdf1DBb8e"
            },
        ...


.. py:attribute:: TransactionReceipt.sender

    The address the transaction was sent from. Where possible, this will be an Account instance instead of a string.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.sender
        <Account object '0x6B5132740b834674C3277aAfa2C27898CbE740f6'>

.. py:attribute:: TransactionReceipt.status

    An :class:`IntEnum <enum.IntEnum>` object representing the status of the transaction:

        * ``1``: Successful
        * ``0``: Reverted
        * ``-1``: Pending
        * ``-2``: Dropped

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.status
        1

.. py:attribute:: TransactionReceipt.timestamp

    The timestamp of the block that this transaction was included in.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.timestamp
        1588957325

.. py:attribute:: TransactionReceipt.trace

    An expanded `transaction trace <https://geth.ethereum.org/docs/dapp/tracing#basic-traces>`_ structLog, returned from the `debug_traceTransaction <https://geth.ethereum.org/docs/rpc/ns-debug#debug_tracetransaction>`_ RPC endpoint. If you are using Infura this attribute is not available.

    Along with the standard data, the structLog also contains the following additional information:

    * ``address``: The address of the contract that executed this opcode
    * ``contractName``: The name of the contract
    * ``fn``: The name of the function
    * ``jumpDepth``: The number of jumps made since entering this contract. The initial function has a value of 1.
    * ``source``: The path and offset of the source code associated with this opcode.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> len(tx.trace)
        239
        >>> tx.trace[0]
        {
            'address': "0x79447c97b6543F6eFBC91613C655977806CB18b0",
            'contractName': "Token",
            'depth': 0,
            'error': "",
            'fn': "Token.transfer",
            'gas': 128049,
            'gasCost': 22872,
            'jumpDepth': 1,
            'memory': [],
            'op': "PUSH1",
            'pc': 0,
            'source': {
                'filename': "contracts/Token.sol",
                'offset': [53, 2053]
            },
            'stack': [],
            'storage': {
            }
        }

.. py:attribute:: TransactionReceipt.txid

    The transaction hash.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.txid
        '0xa8afb59a850adff32548c65041ec253eb64e1154042b2e01e2cd8cddb02eb94f'

.. py:attribute:: TransactionReceipt.txindex

    The integer of the transaction's index position in the block.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.txindex
        0

.. py:attribute:: TransactionReceipt.value

    The value of the transaction, in :func:`Wei <brownie.convert.datatypes.Wei>`.

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.value
        0

TransactionReceipt Methods
**************************

.. py:method:: TransactionReceipt.replace(increment=None, gas_price=None)

    Broadcast an identical transaction with the same nonce and a higher gas price.

    Exactly one of the following arguments must be provided:

    * ``increment``: Multiplier applied to the gas price of the current transaction in order to determine a new gas price
    * ``gas_price``: Absolute gas price to use in the replacement transaction

    For EIP-1559 transactions, the modification is applied to ``max_fee``. The ``priority_fee`` is always multiplied by 1.1 (the minimum increase required to be accepted by a node).

    Returns a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` object.

    .. code-block:: python

        >>> tx = accounts[0].transfer(accounts[1], 100, required_confs=0, gas_price="1 gwei")
        Transaction sent: 0xc1aab54599d7875fc1fe8d3e375abb0f490cbb80d5b7f48cedaa95fa726f29be
          Gas price: 13.0 gwei   Gas limit: 21000   Nonce: 3
        <Transaction object '0xc1aab54599d7875fc1fe8d3e375abb0f490cbb80d5b7f48cedaa95fa726f29be'>

        >>> tx.replace(1.1)
        Transaction sent: 0x9a525e42b326c3cd57e889ad8c5b29c88108227a35f9763af33dccd522375212
          Gas price: 14.3 gwei   Gas limit: 21000   Nonce: 3
        <Transaction '0x9a525e42b326c3cd57e889ad8c5b29c88108227a35f9763af33dccd522375212'>

.. py:classmethod:: TransactionReceipt.info()

    Displays verbose information about the transaction, including event logs and the error string if a transaction reverts.

    .. code-block:: python

        >>> tx = accounts[0].transfer(accounts[1], 100)
        <Transaction object '0x2facf2d1d2fdfa10956b7beb89cedbbe1ba9f4a2f0592f8a949d6c0318ec8f66'>
        >>> tx.info()

        Transaction was Mined
        ---------------------
        Tx Hash: 0x2facf2d1d2fdfa10956b7beb89cedbbe1ba9f4a2f0592f8a949d6c0318ec8f66
        From: 0x5fe657e72E76E7ACf73EBa6FA07ecB40b7312d80
        To: 0x5814fC82d51732c412617Dfaecb9c05e3B823253
        Value: 100
        Block: 1
        Gas Used: 21000

           Events In This Transaction
           --------------------------
           Transfer
              from: 0x5fe657e72E76E7ACf73EBa6FA07ecB40b7312d80
              to: 0x31d504908351d2d87f3d6111f491f0b52757b592
              value: 100

.. py:classmethod:: TransactionReceipt.call_trace(expand=False)

    Display the complete sequence of contracts and functions called while execiting this transaction.

    Each line is formatted as:

    ::

        ContractName.functionName  (external call opcode)  start:stop  [internal / total gas used]


    * ``start``:``stop`` are index values for the :func:`TransactionReceipt.trace <TransactionReceipt.trace>`, showing where the call begins and ends
    * for calls that include subcalls, gas use is displayed as ``[gas used in this frame / gas used in this frame + subcalls]``
    * Calls that terminate with a ``REVERT`` or ``INVALID`` instruction are highlighted in red

    .. code-block:: python

        >>> tx.call_trace()
        Call trace for '0x7824c6032966ca2349d6a14ec3174d48d546d0fb3020a71b08e50c7b31c1bcb1':
        Initial call cost  [21228 gas]
        LiquidityGauge.deposit  0:3103  [64010 / 128030 gas]
        ├── LiquidityGauge._checkpoint  83:1826  [-6420 / 7698 gas]
        │   ├── GaugeController.get_period_timestamp  [STATICCALL]  119:384  [2511 gas]
        │   ├── ERC20CRV.start_epoch_time_write  [CALL]  411:499  [1832 gas]
        │   ├── GaugeController.gauge_relative_weight_write  [CALL]  529:1017  [3178 / 7190 gas]
        │   │   └── GaugeController.change_epoch  697:953  [2180 / 4012 gas]
        │   │       └── ERC20CRV.start_epoch_time_write  [CALL]  718:806  [1832 gas]
        │   └── GaugeController.period  [STATICCALL]  1043:1336  [2585 gas]
        ├── LiquidityGauge._update_liquidity_limit  1929:2950  [45242 / 54376 gas]
        │   ├── VotingEscrow.balanceOf  [STATICCALL]  1957:2154  [2268 gas]
        │   └── VotingEscrow.totalSupply  [STATICCALL]  2180:2768  [6029 / 6866 gas]
        │       └── VotingEscrow.supply_at  2493:2748  [837 gas]
        └── ERC20LP.transferFrom  [CALL]  2985:3098  [1946 gas]

    Setting ``expand=True`` displays an expanded call trace that also includes function inputs and return values for all external calls.

    .. code-block:: python

        >>> history[-1].call_trace(True)

        Call trace for '0x7824c6032966ca2349d6a14ec3174d48d546d0fb3020a71b08e50c7b31c1bcb1':
        Initial call cost  [21228 gas]
        LiquidityGauge.deposit  0:3103  [64010 / 128030 gas]
        ├── LiquidityGauge._checkpoint  83:1826  [-6420 / 7698 gas]
        │   │
        │   ├── GaugeController.get_period_timestamp  [STATICCALL]  119:384  [2511 gas]
        │   │       ├── address: 0x0C41Fc429cC21BC3c826efB3963929AEdf1DBb8e
        │   │       ├── input arguments:
        │   │       │   └── p: 0
        │   │       └── return value: 1594574319
        ...

.. py:classmethod:: TransactionReceipt.traceback()

    Returns an error traceback for the transaction, similar to a regular python traceback. If the transaction did not revert, returns an empty string.

    .. code-block:: python

        >>> tx = >>> Token[0].transfer(accounts[1], "100000 ether")

        Transaction sent: 0x9542e92a904e9d345def311ea52f22c3191816c6feaf7286f9b48081ab255ffa
        Token.transfer confirmed (reverted) - block: 5   gas used: 23956 (100.00%)
        <Transaction object '0x9542e92a904e9d345def311ea52f22c3191816c6feaf7286f9b48081ab255ffa'>

        >>> tx.traceback()
        Traceback for '0x9542e92a904e9d345def311ea52f22c3191816c6feaf7286f9b48081ab255ffa':
        Trace step 99, program counter 1699:
          File "contracts/Token.sol", line 67, in Token.transfer:
            balances[msg.sender] = balances[msg.sender].sub(_value);
        Trace step 110, program counter 1909:
          File "contracts/SafeMath.sol", line 9, in SafeMath.sub:
            require(b <= a);

.. py:classmethod:: TransactionReceipt.error(pad=3)

    Displays the source code that caused the first revert in the transaction, if any.

    * ``pad``: Number of unrelated liness of code to include before and after the relevant source


    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.error()
        Source code for trace step 86:
          File "contracts/SafeMath.sol", line 9, in SafeMath.sub:

                c = a + b;
                require(c >= a);
            }
            function sub(uint a, uint b) internal pure returns (uint c) {
                require(b <= a);
                c = a - b;
            }
            function mul(uint a, uint b) internal pure returns (uint c) {
                c = a * b;

.. py:classmethod:: TransactionReceipt.source(idx, pad=3)

    Displays the associated source code for a given stack trace step.

    * ``idx``: Stack trace step index
    * ``pad``: Number of unrelated liness of code to include before and after the relevant source

    .. code-block:: python

        >>> tx
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>
        >>> tx.source(86)
        Source code for trace step 86:
          File "contracts/SafeMath.sol", line 9, in SafeMath.sub:

                c = a + b;
                require(c >= a);
            }
            function sub(uint a, uint b) internal pure returns (uint c) {
                require(b <= a);
                c = a - b;
            }
            function mul(uint a, uint b) internal pure returns (uint c) {
                c = a * b;


.. py:classmethod:: TransactionReceipt.wait(n)

    Will wait for ``n`` :attr:`confirmations<TransactionReceipt.confirmations>` of the transaction. This has no effect if ``n`` is less than the current amount of confirmations.

.. code-block:: python

        >>> tx
        <Transaction '0x830b842e24efae712b67dddd97633356122c36e6cf2193fcf9f7dc635c4cbe2f'>
        >>> tx.wait(2)
        This transaction already has 3 confirmations.
        >>> tx.wait(6)
        Required confirmations: 6/6
          Transaction confirmed - Block: 17   Gas used: 21000 (0.31%)

``brownie.network.web3``
========================

The ``web3`` module contains a slightly modified version of the web3.py :class:`Web3 <web3.Web3>` class that is used throughout various Brownie modules for RPC communication.

Web3
----

See the `Web3 API documentation <https://web3py.readthedocs.io/en/stable/web3.main.html#web3.Web3>`_ for detailed information on all the methods and attributes available here. This document only outlines methods that differ from the normal :class:`Web3 <web3.Web3>` public interface.

.. py:class:: brownie.network.web3.Web3

    Brownie subclass of :class:`Web3 <web3.Web3>`. An instance is created at ``brownie.network.web3.web`` and available for import from the main package.

    .. code-block:: python

        >>> from brownie import web3
        >>>

Web3 Methods
************

.. py:classmethod:: Web3.connect(uri, timeout=30)

    Connects to a `provider <https://web3py.readthedocs.io/en/stable/providers.html>`_. ``uri`` can be the path to a local IPC socket, a websocket address beginning in ``ws://`` or a URL.

    .. code-block:: python

        >>> web3.connect('https://127.0.0.1:8545')
        >>>

.. py:classmethod:: Web3.disconnect()

    Disconnects from a provider.

    .. code-block:: python

        >>> web3.disconnect()
        >>>

Web3 Attributes
***************

.. py:classmethod:: Web3.chain_uri

    Returns a `BIP122 blockchain URI <https://github.com/bitcoin/bips/blob/master/bip-0122.mediawiki>`_ for the active chain.

    .. code-block:: python

        >>> web3.chain_uri
        'blockchain://a82ff4a4184a7b9e57aba1ae1ef91214c7d14a1040f4e1df8c0ec95f87a5bb62/block/66760b538b3f02f6fbd4a745b3943af9fda982f2b8b26b502180ed96b2c7f52d'

.. py:classmethod:: Web3.genesis_hash

    Returns the hash of the genesis block for the active chain, as a string without a `0x` prefix.

    .. code-block:: python

        >>> web3.genesis_hash
        '41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d'

.. py:classmethod:: Web3.supports_traces

    Boolean indicating if the currently connected node client supports the `debug_traceTransaction <https://geth.ethereum.org/docs/rpc/ns-debug#debug_tracetransaction>`_ RPC endpoint.

    .. code-block:: python

        >>> web3.supports_traces
        True


Web3 Internals
**************

.. py:attribute:: Web3._mainnet

    Provides access to a ``Web3`` instance connected to the ``mainnet`` network as defined in the configuration file. Used internally for `ENS <https://ens.domains/>`_ lookups.

    Raises :func:`MainnetUndefined <brownie.exceptions.MainnetUndefined>` if the ``mainnet`` network is not defined.

Internal Methods
----------------

.. py:method:: brownie.network.web3._resolve_address(address)

    Used internally for standardizing address inputs. If ``address`` is a string containing a ``.`` Brownie will attempt to resolve an `ENS domain name <https://ens.domains/>`_ address. Otherwise, returns the result of :func:`convert.to_address <brownie.convert.to_address>`.
