.. _build-folder:

================
The Build Folder
================

Each project has a ``build/`` folder that contains various data files. If you are integrating a third party tool or hacking on the Brownie source code, it can be valuable to understand how these files are structured.

.. _build-folder-compiler:

Compiler Artifacts
==================

Brownie generates compiler artifacts for each contract within a project, which are stored in the ``build/contracts`` folder. The structure of these files are as follows:

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

This raw data is available within Brownie through the `build <api-project-build>`_ module. If the contract was minified before compiling, Brownie will automatically adjust the source map offsets in ``pcMap`` and ``coverageMap`` to fit the current source.

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

All compiler artifacts include a ``coverageMap`` which is used when evaluating test coverage. It is structured as a nested dictionary in the following format:

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

Deployment Artifacts
====================

Each time a contract is deployed to a network where :ref:`persistence<nonlocal-networks-contracts>` is enabled, Brownie saves a copy of the :ref:`compiler artifact<build-folder-compiler>`_ used for deployment. In this way accurate deployment data is maintained even if the contract's source code is later modified.

Deployment artifacts are stored at:

::

    build/deployments/[NETWORK_NAME]/[ADDRESS].json

When instantiating :ref:`Contract<api-network-contract>` objects from deployment artifacts, Brownie parses the files in order of creation time. If the ``contractName`` field in an artifact gives a name that longer exists within the project, the file is deleted.

Test Results and Coverage Data
==============================

The ``build/test.json`` file holds information about unit tests and coverage evaluation. It has the following format:

.. code-block:: javascript

    {
        "contracts": {
            "contractName": "0xff" // Hash of the contract source
        },
        //
        "tests": {
            "tests/path/of/test_file.py": {
                "coverage": true, // Has coverage eval been performed for this module?
                "isolated": [], // List of contracts deployed when executing this module. Used to determine if the tests must be re-run.
                "results": ".....", // Test results. Follows the same format as pytest's output (.sfex)
                "sha1": "0xff", // Hash of the module
                "txhash": [] // List of transaction hashes generated when running this module.
            },
        },
        // Coverage data for individual transactions
        "tx": {
            "0xff": { // Transaction hash
                "ContractName": {
                    // Coverage map indexes (see below)
                    "path/to/contract.sol": [
                        [], // statements
                        [], // branches that did not jump
                        []  // branches that did jump
                    ]
                }
            }
        }
    }

.. _tests-coverage-map-indexes:

Coverage Map Indexes
--------------------

In tracking coverage, Brownie produces a set of coverage map indexes for each transaction. They are represented as lists of lists, each list containing key values that correspond to that contract's :ref:`coverage map<compile-coverage-map>`. As an example, look at the following transaction coverage data:

.. code-block:: javascript

    {
        "ae6ccafbd0b0c8cf2eb623e390080854755f3fa7": {
            "Token": {
                // Coverage map indexes (see below)
                "contracts/Token.sol": [
                    [1, 3],
                    [],
                    [5]
                ],
                "contracts/SafeMath.sol": [
                    [8],
                    [11],
                    [11]
                ],
            }
        }
    }

Here we see that within the ``Token`` contract:

* Statements 1 and 3 were executed in ``"contracts/Token.sol"``, as well as statement 8 in ``"contracts/SafeMath.sol"``
* In ``"contracts/Token.sol"``, there were no branches that were seen and did not jump, branch 5 was seen and did jump
* In ``"contracts/SafeMath.sol"``, branch 11 was seen both jumping and not jumping

To convert these indexes to source offsets, we check the :ref:`coverage map<compile-coverage-map>` for Token. For example, here is branch 11:

.. code-block:: javascript

    {
        "contracts/SafeMath.sol": {
            "SafeMath.add": {
                "11": [147, 153, true]
            }
        }
    }

From this we know that the branch is within the ``add`` function, and that the related source code starts at position 147 and ends at 153. The final boolean indicates whether a jump means the branch evaluated truthfully of falsely - in this case, a jump means it evaluated ``True``.

Installed ethPM Package Data
============================

The ``build/packages.json`` file holds information about installed ethPM packages. It has the following format:

.. code-block:: javascript

    {
        "packages": {
            "package_name": {
                "manifest_uri": "ipfs://",  // ipfs URI of the package manifest
                "registry_address": "",  // ethPM registry address the package was installed from
                "version": ""  // package version string
            },
            ...
        },
        "sources": {
            "path/to/ContractFile.sol": {
                "md5": "",  // md5 hash of the source file at installation
                "packages": []  // installed packages that include this source file
            },
            ...
        }
    }
