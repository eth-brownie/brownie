.. _config:

=======================
Editing the Config File
=======================

Every project has a file ``brownie-config.json`` that holds all the configuration settings.

The defaut configuration is as follows:

.. literalinclude:: ../config.json
    :linenos:
    :language: json

Settings
========

The following settings are available:

.. py:attribute:: default_network

    The default network to initialize when brownie is loaded.

.. py:attribute:: networks

    Defines the available networks. The following properties can be set:

    * ``host``: The address and port of the RPC API you wish to connect to. If using `Infura <https://infura.io/>`__, be sure to obtain and include your own network access token in the address.
    * ``test-rpc``: Optional. If given, this command will be run in a shell when brownie is started. In this way you can initialize Ganache or another local environment automatically when Brownie starts.
    * ``persist``: Optional. If set to true, information such as addresses that contracts are deployed at will be saved in the ``environments/`` folder so they can be accessed the next time you run Brownie. See :ref:`persist`.

.. py:attribute:: solc

    Properties relating to the solc compiler.

    * ``optimize``: Set to true if you wish to use contract optimization.
    * ``runs``: The number of times the optimizer should run.

.. py:attribute:: logging

    Default logging levels for each brownie mode.

    * ``tx``: Transaction information
    * ``exc``: Exception information

    Valid values range from 0 (nothing) to 2 (detailed). When given as a 2 item list, it corresponds to normal/verbose. When given as a single value, adding the '--verbose' tag will do nothing.

Default Settings
================

The default settings are found in ``config.json`` in the brownie install folder. Omitting any setting within a project's configuration file will cause Brownie to use the default setting instead.
