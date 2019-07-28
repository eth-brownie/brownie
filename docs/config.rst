.. _config:

======================
The Configuration File
======================

Every project has a file ``brownie-config.json`` that holds all the configuration settings. The defaut configuration is as follows.

.. literalinclude:: ../brownie/data/config.json
    :linenos:
    :language: json

When using the Brownie console or writing scripts, you can view and edit configuration settings through the ``config`` dict. Any changes made in this way are temporary and will be reset when you exit Brownie or reset the network.

Settings
========

The following settings are available:

.. py:attribute:: networks

    Defines the available networks. The following properties can be set:

    * ``host``: The address and port of the RPC API you wish to connect to. If using `Infura <https://infura.io/>`__, be sure to obtain and include your own network access token in the address.
    * ``gas_price``: The default gas price for all transactions. If left as ``false`` the gas price will be determined using ``web3.eth.gasPrice``.
    * ``gas_limit``: The default gas limit for all transactions. If left as ``false`` the gas limit will be determined using ``web3.eth.estimateGas``.
    * ``broadcast_reverting_tx``: Optional. If set to ``false``, transactions that would revert will instead raise a ``VirtualMachineError``.

    Each network can optionally include a dictionary under the key ``test-rpc``, that outlinies settings for how the local RPC client is loaded. If not included, Brownie will not attempt to launch or attach to the process. See :ref:`test-rpc` for more details. ``test-rpc`` properties include:

    * ``cmd``: The command-line argument used to load the client. You can add any extra flags here as needed.
    * ``port``: Port the client should listen on.
    * ``gas_limit``: Block gas limit.
    * ``accounts``: The number of funded accounts in ``web3.eth.accounts``.
    * ``evm_version``: The EVM version to compile for. If ``null`` the most recent one is used. Possible values are ``byzantium``, ``constantinople`` and ``petersburg``.
    * ``mnemonic``: Local accounts are derived from this mnemonic. If set to ``null``, you will have different local accounts each time Brownie is run.

.. py:attribute:: network_defaults

    Default networks settings that are are applied to all networks. Any network-specific settings will override these.

    You **must** specify a ``name`` property. This is the default network that Brownie uses when loaded, unless one is explicitely declared at the command line.

.. _config-solc:

.. py:attribute:: solc

    Properties relating to the solc compiler. See :ref:`compiler settings<compile_settings>` for more information.

    * ``version``: The version of solc to use. Should be given as a string in the format ``0.x.x``. If set to ``null``, the version is set based on the contract pragma. Brownie supports solc versions ``>=0.4.22``.
    * ``evm_version``: The EVM version to compile for. If ``null`` the most recent one is used. Possible values are ``byzantium``, ``constantinople`` and ``petersburg``.
    * ``optimize``: Set to ``true`` if you wish to enable compiler optimization.
    * ``runs``: The number of times the optimizer should run.
    * ``minify_source``: If ``true``, contract source is minified before compiling.

.. py:attribute:: pytest

    Properties that only affect Brownie's configuration when running tests. See :ref:`test configuration settings<test_settings>` for more information.

    * ``gas_limit``: Replaces the default network gas limit.
    * ``default_contract_owner``: If ``false``, deployed contracts will not remember the account that they were created by and you will have to supply a ``from`` kwarg for every contract transaction.
    * ``broadcast_reverting_tx``: Replaces the default network setting for broadcasting reverting transactions.
    * ``revert_traceback``: if ``true``, unhandled ``VirtualMachineError`` exceptions will include a full traceback for the reverted transaction.

.. py:attribute:: colors

    Defines the colors associated with specific data types when using Brownie. Setting a value as an empty string will use the terminal's default color.
