.. _compile:

===================
Compiling Contracts
===================

To compile a project:

::

    $ brownie compile

Each time the compiler runs, Brownie compares hashes of the contract source code against the existing compiled versions.  If a contract has not changed it will not be recompiled. If you wish to force a recompile of the entire project, use ``brownie compile --all``.

.. _compile_settings:

Compiler Settings
=================

Settings for the compiler are found in ``brownie-config.json``:

.. code-block:: javascript

    {
        "solc":{
            "version": "0.5.10",
            "evm_version": null,
            "optimize": true,
            "runs": 200,
            "minify_source": false
        }
    }

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

Build JSON Format
=================

.. note::

    Unless you are integrating a third party tool or hacking on the Brownie source code, you won't need to understand the compiled contract format. If you're just using Brownie for developing a project you can skip the rest of this section.

Each contract has it's own JSON file stored in the ``build/contracts`` folder. The format of this file is as follows:

.. code-block:: javascript

    {
        'abi': [], // contract ABI
        'allSourcePaths': [], // relative paths to every related contract source code file
        'ast': {}, // the AST object
        'bytecode': "0x00", // bytecode object as a hex string, used for deployment
        'bytecodeSha1': "", // hash of bytecode without final metadata
        'compiler': {}, // information about the compiler
        'contractName': "", // name of the contract
        'coverageMap': {}, // map for evaluating unit test coverage
        'deployedBytecode': "0x00", // bytecode as hex string after deployment
        'deployedSourceMap': "", // source mapping of the deployed bytecode
        'dependencies': [], // contracts and libraries that this contract inherits from or is linked to
        'offset': [], // source code offsets for this contract
        'opcodes': "", // deployed contract opcodes list
        'pcMap': [], // program counter map
        'sha1': "", // hash of the contract source, used to check if a recompile is necessary
        'source': "", // compiled source code as a string
        'sourceMap': "", // source mapping of undeployed bytecode
        'sourcePath': "", // relative path to the contract source code file
        'type': "" // contract, library, interface
    }

This raw data is available through the `build <api-project-build>`_ module. If the contract was minified before compiling, Brownie will automatically adjust the source map offsets in ``pcMap`` and ``coverageMap`` to fit the current source.

.. code-block:: python

    >>> from brownie.project import build
    >>> token_json = build.get("Token")
    >>> token_json['contractName']
    "Token"

.. _compile-pc-map:

Program Counter Map
-------------------

Brownie generates an expanded version of the `deployed source mapping <https://solidity.readthedocs.io/en/latest/miscellaneous.html#source-mappings>`_ that it uses for debugging and test coverage evaluation. It is structured as a dictionary of dictionaries, where each key is a program counter as given by ``debug_traceTransaction``.

If a value is ``false`` or the type equivalent, the key is not included.

.. code-block:: javascript

    {
        'pc': {
            'op': "", // opcode string
            'path': "", // relative path to the contract source code
            'offset': [0, 0], // source code start and stop offsets
            'fn': str, // name of the related method
            'jump': "", // jump instruction as given in the sourceMap (i, o)
            'value': "0x00", // hex string value of the instruction
            'statement': 0, // statement coverage index
            'branch': 0 // branch coverage index
        }
    }

.. _compile-coverage-map:

Coverage Map
------------

All build files include a ``coverageMap`` which is used when evaluating test coverage. It is structured as a nested dictionary in the following format:

.. code-block:: javascript

    {
        "statements": {
            "/path/to/contract/file.sol": {
                "ContractName.functionName": {
                    "index": [start, stop]  // source offsets
                }
            }
        },
        "branches": {
            "/path/to/contract/file.sol": {
                "ContractName.functionName": {
                    "index": [start, stop, bool]  // source offsets, jump boolean
                }
            }
        }
    }


* Each ``statement`` index exists on a single program counter step. The statement is considered to have executed when the corresponding opcode executes within a transaction.
* Each ``branch`` index is found on two program counters, one of which is always a ``JUMPI`` instruction. A transaction must run both opcodes before the branch is considered to have executed. Whether it evaluates true or false depends on if the jump occurs.

See :ref:`tests-coverage-map-indexes` for more information.
