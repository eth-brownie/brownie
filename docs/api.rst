.. _api:

===========
Brownie API
===========

The following classes and methods are available when writing brownie scripts or using the console.

.. warning::

    The API documentation is currently being updated. Some endpoints may be missing, some information may be out of date. The update should be finished in the next few days.. Sorry!

.. note::

    From the console you can call ``dir`` to see available methods and attributes for any class. By default, callables are highlighed in cyan and attributes in blue. You can also call ``help`` on any class or method to view information on it's functionality.

.. code-block:: python

    >>> dir()
    [SafeMath, Token, a, accounts, alert, check, config, dir, gas, history, logging, reset, rpc, run, web3, wei]

.. toctree::

    :maxdepth: 2
    Brownie <api-brownie.rst>
    Network <api-network.rst>
    Project <api-project.rst>
    Test <api-test.rst>
    Types <api-types.rst>
    Utils <api-utils.rst>
