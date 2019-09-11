.. _config:

======================
The Configuration File
======================

Every project has a file ``brownie-config.json`` that holds all the configuration settings. The defaut configuration is as follows.

.. literalinclude:: ../brownie/data/config.json
    :linenos:
    :language: json

When using the Brownie console or writing scripts, you can view and edit configuration settings through the ``config`` dict. Any changes made in this way are temporary and will be reset when you exit Brownie or reset the network.

.. note::

    If you are experiencing errors or warnings related to the configuration file, delete it and then run ``brownie init`` from the root folder of your project. This will create a clean copy of the config file.

Settings
========

The following settings are available:

.. py:attribute:: network

    Defines the available networks and how Brownie interacts with them.

    * ``default``:  The default network that brownie connects to when loaded. If a different network is required, you can override this setting with the ``--network`` flag in the command line.

    .. py:attribute:: network.settings

        Default settings for every network. The following properties can be set:

        * ``gas_price``: The default gas price for all transactions. If left as ``false`` the gas price will be determined using ``web3.eth.gasPrice``.
        * ``gas_limit``: The default gas limit for all transactions. If left as ``false`` the gas limit will be determined using ``web3.eth.estimateGas``.
        * ``reverting_tx_gas_limit``: The gas limit to use when a transaction would revert. If set to ``false``, transactions that would revert will instead raise a ``VirtualMachineError``.

    .. py:attribute:: network.networks

        Settings specific to individual networks. All values outlined above in ``settings`` are also valid here and will override the defaults.

        Additionally, you must include a host setting in order to connect to that network:

        * ``host``: The address and port of the RPC API you wish to connect to. If using `Infura <https://infura.io/>`__, be sure to obtain and include your own network access token in the address.

        .. py:attribute:: network.networks.test_rpc

            An optional dictionary outlining settings for how the local RPC client is loaded. If not included, Brownie will not attempt to launch or attach to the process. See :ref:`test-rpc` for more details. ``test-rpc`` properties include:

            * ``cmd``: The command-line argument used to load the client. You can add any extra flags here as needed.
            * ``port``: Port the client should listen on.
            * ``gas_limit``: Block gas limit.
            * ``accounts``: The number of funded accounts in ``web3.eth.accounts``.
            * ``evm_version``: The EVM version to compile for. If ``null`` the most recent one is used. Possible values are ``byzantium``, ``constantinople`` and ``petersburg``.
            * ``mnemonic``: Local accounts are derived from this mnemonic. If set to ``null``, you will have different local accounts each time Brownie is run.

.. _config-solc:

.. py:attribute:: compiler

    Compiler settings. See :ref:`compiler settings<compile_settings>` for more information.

    .. py:attribute:: compiler.solc

        Settings specific to the Solidity compiler. At present this is the only compiler supported by Brownie.

        * ``version``: The version of solc to use. Should be given as a string in the format ``0.x.x``. If set to ``null``, the version is set based on the contract pragma. Brownie supports solc versions ``>=0.4.22``.
        * ``evm_version``: The EVM version to compile for. If ``null`` the most recent one is used. Possible values are ``byzantium``, ``constantinople`` and ``petersburg``.
        * ``optimize``: Set to ``true`` if you wish to enable compiler optimization.
        * ``runs``: The number of times the optimizer should run.
        * ``minify_source``: If ``true``, contract source is minified before compiling.

.. py:attribute:: pytest

    Properties that only affect Brownie's configuration when running tests. See :ref:`test configuration settings<test_settings>` for more information.

    * ``gas_limit``: Replaces the default network gas limit.
    * ``default_contract_owner``: If ``false``, deployed contracts will not remember the account that they were created by and you will have to supply a ``from`` kwarg for every contract transaction.
    * ``reverting_tx_gas_limit``: Replaces the default network setting for the gas limit on a tx that will revert.
    * ``revert_traceback``: if ``true``, unhandled ``VirtualMachineError`` exceptions will include a full traceback for the reverted transaction.

.. py:attribute:: colors

    Defines the colors associated with specific data types when using Brownie. Setting a value as an empty string will use the terminal's default color.
