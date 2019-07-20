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
    * ``test-rpc``: Optional. If given, this command will be run in a shell when brownie is started. In this way you can initialize Ganache or another local environment automatically when Brownie starts.
    * ``gas_price``: The default gas price for all transactions. If left as false the gas price will be determined using ``web3.eth.gasPrice``.
    * ``gas_limit``: The default gas limit for all transactions. If left as false the gas limit will be determined using ``web3.eth.estimateGas``.
    * ``broadcast_reverting_tx``: Optional. If set to ``false``, transactions that would revert will instead raise a ``VirtualMachineError``.

.. py:attribute:: network_defaults

    Default networks settings, used when specific properties aren't defined for individual networks.

    You **must** specify a ``name`` property. This is the default network to use when brownie is loaded.

.. py:attribute:: solc

    Properties relating to the solc compiler.

    * ``optimize``: Set to true if you wish to use contract optimization.
    * ``runs``: The number of times the optimizer should run.
    * ``version``: The version of solc to use. Should be written as ``v0.x.x``. If the specified version is not present, it will be installed when Brownie loads.
    * ``minify_source``: If set to true, contracts are minified before compiling. This allows you to modify formatting and comments without triggering a recompile.

.. py:attribute:: test

    Properties that affect only affect Brownie's configuration when running tests. See Test :ref:`test_settings` for detailed information on the effects and implications of these settings.

    * ``gas_limit``: Replaces the default network gas limit.
    * ``default_contract_owner``: If ``false``, deployed contracts will not remember the account that they were created by and you will have to supply a ``from`` kwarg for every contract transaction.
    * ``broadcast_reverting_tx``: Replaces the default network setting for broadcasting reverting transactions.
    * ``revert_traceback``: if ``true``, unhandled ``VirtualMachineError`` exceptions will include a full traceback for the reverted transaction.

.. py:attribute:: colors

    Defines the colors associated with specific data types when using Brownie. Setting a value as an empty string will use the terminal's default color.
