.. _compile:

===================
Compiling Contracts
===================

Each time brownie is run it will check the existing contract code against the last compiled version. Any source code that has changed will be recompiled.

Modifying the compiler version or optomization settings will cause a full recompile of the project.

Compiled data is stored in the ``build/contracts`` folder. You can force a recompile by deleting this folder.

Compiled JSON Structure
=======================

Each contract will have it's own ``.json`` file in the ``build/contracts`` folder.  The format of this file is as follows:

.. code-block:: javascript

    {
        'abi': [], // contract ABI
        'ast': {}, // the AST object
        'bytecode': "0x00", // bytecode object as a hex string, used for deployment
        'compiler': {}, // information about the compiler
        'contractName': "", // name of the contract
        'deployedBytecode': "0x00", // bytecode as hex string after deployment
        'deployedSourceMap': "", // source mapping of the deployed bytecode
        'networks': {}, // contract locations for persistent environments
        'opcodes': "", // deployed contract opcodes list
        'pcMap': [], // program counter map (see below)
        'sha1': "", // hash of the contract source, used to check if a recompile is necessary
        'source': "", // source code as a string
        'sourceMap': "", // source mapping of undeployed bytecode
        'sourcePath': "", // relative path to the contract file
        'type': "" // contract, library, interface
    }

Program Counter Map
===================

Brownie creates an expanded version of the deployed source mapping to aid in debugging and test coverage evaluation. It is structured as a list of dictionaries in the following format:

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
