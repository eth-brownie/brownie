.. _compile:

===================
Compiling Contracts
===================

To compile a project:

::

    $ brownie compile

Each time the compiler runs, Brownie compares hashes of the contract source code against the existing compiled versions.  If a contract has not changed it will not be recompiled. If you wish to force a recompile of the entire project, use ``brownie compile --all``.

The compiler version is set in ``brownie-config.json``. If the required version is not present, it will be installed when Brownie loads.

.. code-block:: javascript

    {
        "solc":{
            "optimize": true,
            "runs": 200,
            "version": "0.5.7",
            "minify_source": false
        }
    }

Modifying the compiler version or optimization settings will result in a full recompile of the project.

If ``minify_source`` is ``true``, the contract source is minified before compiling. Brownie will then minify the source code before checking the hashes to determine if a recompile is necessary. This allows you to modify formatting and comments without triggering a recompile.

.. _compile-json:

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

See :ref:`coverage` for more information on test coverage evaluation.
