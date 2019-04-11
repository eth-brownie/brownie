.. _config:

=======================
Editing the Config File
=======================

Every project has a file ``brownie-config.json`` that holds all the configuration settings.

The defaut configuration is as follows. When using the brownie console or writing scripts, you can view and edit configuration settings through the ``config`` dict. Any changes made in this way are temporary and will be reset when you exit brownie or reset the network.

.. literalinclude:: ../brownie/data/config.json
    :linenos:
    :language: json

Settings
========

The following settings are available:

.. py:attribute:: networks

    Defines the available networks. The following properties can be set:

    * ``host``: The address and port of the RPC API you wish to connect to. If using `Infura <https://infura.io/>`__, be sure to obtain and include your own network access token in the address.
    * ``persist``: If set to true, information such as addresses that contracts are deployed at will be saved in the ``build/`` folder so they can be accessed the next time you run Brownie. See :ref:`persist`.
    * ``test-rpc``: Optional. If given, this command will be run in a shell when brownie is started. In this way you can initialize Ganache or another local environment automatically when Brownie starts.
    * ``gas_price``: The default gas price for all transactions. If left as false the gas price will be determined using ``web3.eth.gasPrice``.
    * ``gas_limit``: The default gas limit for all transactions. If left as false the gas limit will be determined using ``web3.eth.estimateGas``.

.. py:attribute:: network_defaults

    Default networks settings, used when specific properties aren't defined for individual networks.

    You must specify a ``name`` property. This is the default network to use when brownie is loaded.

.. py:attribute:: solc

    Properties relating to the solc compiler.

    * ``optimize``: Set to true if you wish to use contract optimization.
    * ``runs``: The number of times the optimizer should run.
    * ``version``: The version of solc to use. Should be written as ``v0.x.x``.

.. py:attribute:: test

    Properties that affect only affect Brownie's configuration when running scripts and tests. See :ref:`test` for detailed information on the effects and implications of these settings.

    * ``always_transact``: If ``true``, calls to ``view`` and ``pure`` functions will still execute as transactions during tests.

    * ``gas_limit``: If set to an integer, this value will over-ride the default gas limit setting when running tests.

    * ``default_contract_owner``: If ``false``, deployed contracts will not remember the account that they were created by and you will have to supply a ``from`` kwarg for every contract transaction.

.. py:attribute:: logging

    Default logging levels for each brownie mode.

    * ``tx``: Transaction information
    * ``exc``: Exception information

    Valid values range from 0 (nothing) to 2 (detailed). When given as a 2 item list, it corresponds to normal/verbose. When given as a single value, adding the '--verbose' tag will do nothing.

.. py:attribute:: colors

    Defines the colors associated with specific data types when using Brownie. Setting a value as an empty string will use the terminal's default color.

Default Settings
================

When you create a new project the configuration file is copied from ``config.json`` in the brownie install folder. Modifying this file will change the default settings for all future projects. Removing any setting within a project's local configuration file will cause Brownie to use the default setting instead.
