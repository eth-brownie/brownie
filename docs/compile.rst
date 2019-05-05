.. _compile:

===================
Compiling Contracts
===================

To compile a project:

::

    $ brownie compile

Each time the compiler runs, Brownie compares hashes of the contract source code against the existing compiled versions.  If a contract has not changed it will not be recompiled.  If you wish to force a recompile of the entire project, use ``brownie compile --all``.

Modifying the compiler version or optomization settings within the project config file will result in a full recompile of the project.

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
        'deployedBytecode': "0x00", // bytecode as hex string after deployment
        'deployedSourceMap': "", // source mapping of the deployed bytecode
        'opcodes': "", // deployed contract opcodes list
        'pcMap': [], // program counter map
        'sha1': "", // hash of the contract source, used to check if a recompile is necessary
        'source': "", // source code as a string
        'sourceMap': "", // source mapping of undeployed bytecode
        'sourcePath': "", // absolute path to the contract source code file
        'type': "" // contract, library, interface
    }

This raw data is available through the :ref:`api-project-build` object:

.. code-block:: python

    >>> from brownie.project.build import Build
    >>> build = Build()
    >>> token_json = build["Token"]
    >>> token_json.keys()
    dict_keys(['abi', 'allSourcePaths', 'ast', 'bytecode', 'compiler', 'contractName', 'coverageMap', 'deployedBytecode', 'deployedSourceMap', 'networks', 'opcodes', 'pcMap', 'sha1', 'source', 'sourceMap', 'sourcePath', 'type'])

Program Counter Map
-------------------

Brownie generates an expanded version of the deployed source mapping that it uses for debugging and test coverage evaluation. It is structured as a list of dictionaries in the following format:

.. code-block:: javascript

    {
        'contract': "", // relative path to the contract source code
        'jump': "", // jump instruction as supplied in the sourceMap (-,i,o)
        'op': "", // opcode string
        'pc': 0, // program counter as given by debug_traceTransaction
        'start': 0, // source code start offset
        'stop': 0, // source code stop offset
        'value': "0x00" // hex string value of the instruction, if any
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
