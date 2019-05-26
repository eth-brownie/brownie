.. _compile:

===================
Compiling Contracts
===================

To compile a project:

::

    $ brownie compile

Each time the compiler runs, Brownie compares hashes of the contract source code against the existing compiled versions.  If a contract has not changed it will not be recompiled.  If you wish to force a recompile of the entire project, use ``brownie compile --all``.

The compiler version is set in ``brownie-config.json``. If the required version is not present, it will be installed when Brownie loads.

.. code-block:: javascript

    {
        "solc":{
            "optimize": true,
            "runs": 200,
            "version": "0.5.7"
        }
    }

Modifying the compiler version or optimization settings will result in a full recompile of the project.

.. _compile-json:

Compiled JSON Format
====================

.. note::

    Unless you are integrating a third party tool or hacking on the Brownie source code, you won't need to understand the compiled contract format. If you're just using Brownie for developing a project you can skip the rest of this section.

Each contract will have it's own ``.json`` file stored in the ``build/contracts`` folder. The format of this file is as follows:

.. code-block:: javascript

    {
        'abi': [], // contract ABI
        'allSourcePaths': [], // absolute paths to every related contract source code file
        'ast': {}, // the AST object
        'bytecode': "0x00", // bytecode object as a hex string, used for deployment
        'bytecodeSha1': "", // hash of bytecode without final metadata
        'compiler': {}, // information about the compiler
        'contractName': "", // name of the contract
        'coverageMap': {}, // map for evaluating unit test coverage
        'coverageMapTotals': {}, // total per-function counts for coverage map items
        'deployedBytecode': "0x00", // bytecode as hex string after deployment
        'deployedSourceMap': "", // source mapping of the deployed bytecode
        'dependencies': [], // contracts and libraries that this contract inherits is linked to
        'fn_offsets': {}, // source code offsets for contract functions
        'offset': [], // source code offsets for this contract
        'opcodes': "", // deployed contract opcodes list
        'pcMap': [], // program counter map
        'sha1': "", // hash of the contract source, used to check if a recompile is necessary
        'source': "", // source code as a string
        'sourceMap': "", // source mapping of undeployed bytecode
        'sourcePath': "", // absolute path to the contract source code file
        'type': "" // contract, library, interface
    }

This raw data is available through the :ref:`api-project-build` module:

.. code-block:: python

    >>> from brownie.project import build
    >>> token_json = build.get("Token")
    >>> token_json['contractName']
    "Token"

Program Counter Map
-------------------

Brownie generates an expanded version of the deployed source mapping that it uses for debugging and test coverage evaluation. It is structured as a dictionary of dictionaries, where each key is a program counter as given by ``debug_traceTransaction``.

.. code-block:: javascript
    {
        'pc': {
            'path': "", // relative path to the contract source code
            'op': "", // opcode string
            'offset': [0, 0], // source code start and stop offsets
            'fn': str, // name of the related method, if any
            'jump': "", // jump instruction as supplied in the sourceMap, if any (i,o)
            'value': "0x00" // hex string value of the instruction, if any
        }
    }

Coverage Map
------------

All build files include a field ``coverageMap`` which is used when evaluating test coverage. It is structured as a nested dictionary in the following format:

.. code-block:: javascript

    {
        "/path/to/contract/file.sol": {
            "functionName": {
                "fn": {},
                "line": [{}, {}, {}],
                "total": 0
            }
        }
    }

Each dictionary within ``fn`` and ``line`` are the actual maps, structured as follows:

.. code-block:: javascript

    {
        'jump': false, // pc of the JUMPI instruction, if it is a jump - otherwise false
        'pc': [], // list of opcode program counters tied to the map item
        'start': 0, // associated source code start offset
        'stop': 0 // associated source code stop offset
    }

See :ref:`coverage` for more information on test coverage evaluation.
