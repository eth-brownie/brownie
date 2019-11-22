.. _compile:

===================
Compiling Contracts
===================

To compile a project:

::

    $ brownie compile

Each time the compiler runs, Brownie compares hashes of the contract source code against the existing compiled versions.  If a contract has not changed it will not be recompiled. If you wish to force a recompile of the entire project, use ``brownie compile --all``.

.. note::

    All of a project's contract sources must be placed inside the ``contracts/`` folder. Attempting to import sources from outside this folder will result in a compiler error.

.. _compile_settings:

Compiler Settings
=================

Settings for the compiler are found in ``brownie-config.yaml``:

.. code-block:: yaml

    solc:
        version: 0.5.10
        evm_version: null
        optimize: true
        runs: 200
        minify_source: false

Modifying any compiler settings will result in a full recompile of the project.

Setting the Compiler Version
----------------------------

.. note::

    Brownie supports Solidity versions ``>=0.4.22``.

If a compiler version is set in the configuration file, all contracts in the project are compiled using that version. It is installed automatically if not already present. The version should be given as a string in the format ``0.x.x``.

If the version is set to ``null``, Brownie looks at the `version pragma <https://solidity.readthedocs.io/en/v0.5.10/layout-of-source-files.html?highlight=pragma#version-pragma>`_ of each contract and uses the latest matching compiler version that has been installed. If no matching version is found, the most recent release is installed.

Setting the version via pragma allows you to use multiple versions in a single project. When doing so, you may encounter compiler errors when a contract imports another contract that is meant to compile on a higher version. A good practice in this situation is to import `interfaces <https://solidity.readthedocs.io/en/v0.5.10/layout-of-source-files.html?highlight=pragma#version-pragma>`_ rather than actual contracts when possible, and set all interface pragmas as ``>=0.4.22``.

The EVM Version
---------------

By default, ``evm_version`` is set to ``null``. Brownie uses ``byzantium`` when compiling versions ``<=0.5.4`` and ``petersburg`` for ``>=0.5.5``.

If you wish to use a newer compiler version on a network that has not yet forked you can set the EVM version manually. Valid options are ``byzantium``, ``constantinople`` and ``petersburg``.

See the `Solidity documentation <https://solidity.readthedocs.io/en/latest/using-the-compiler.html#setting-the-evm-version-to-target>`_ for more info on the different EVM versions.

Compiler Optimization
---------------------

Compiler optimization is enabled by default. Coverage evaluation was designed using optimized contracts - there is no need to disable it during testing.

See the `Solidity documentation <https://solidity.readthedocs.io/en/latest/miscellaneous.html#internals-the-optimiser>`_ for more info on the ``solc`` optimizer.

Source Minification
-------------------

If ``minify_source`` is ``true``, the contract source is minified before compiling. Each time Brownie is loaded it will then minify the current source code before checking the hashes to determine if a recompile is necessary. This allows you to modify code formatting and comments without triggering a recompile, at the cost of increased load times from recalculating source offsets.

.. _compile-json:

Installing the Compiler
=======================

If you wish to manually install a different version of ``solc``:

.. code-block:: python

    >>> from brownie.project.compiler import install_solc
    >>> install_solc("0.5.10")
