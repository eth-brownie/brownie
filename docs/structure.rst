.. _structure:

======================
Structure of a Project
======================

Every Brownie project includes the following folders:

    * ``contracts/``: Contract sources
    * ``interfaces/``: Interface sources
    * ``scripts/``: Scripts for deployment and interaction
    * ``tests/``: Scripts for testing the project

The following folders are also created, and used internally by Brownie for managing the project. You should not edit or delete files within these folders.

    * ``build/``: Project data such as compiler artifacts and unit test results
    * ``reports/``: JSON report files for use in the GUI

See :ref:`build-folder` for more information about Brownie internal project folders.

If you require a different organization for your project, you can adjust the subdirectory names within the project :ref:`configuration file <config-project-structure>`.

``contracts/``
==============

The ``contracts`` folder holds all contract source files for the project. Each time Brownie is run, it checks for new or modified files within this folder. If any are found, they are compiled and included within the project.

Contracts may be written in Solidity (with a ``.sol`` extension) or Vyper (with a ``.vy`` extension).

``interfaces/``
===============

The ``interfaces`` folder holds interface source files that may be referenced by contract sources, but which are not considered to be primary components of the project. Adding or modifying an interface source only triggers a recompile if the interface is required by a contract.

Interfaces may be written in `Solidity <https://solidity.readthedocs.io/en/latest/contracts.html#interfaces>`_ (``.sol``) or `Vyper <https://vyper.readthedocs.io/en/latest/structure-of-a-contract.html#interfaces>`_ (``.vy``), or supplied as a `JSON encoded ABI <https://solidity.readthedocs.io/en/latest/abi-spec.html#json>`_ (``.json``).

``scripts/``
============

The ``scripts`` folder holds Python scripts used for deploying contracts, or to automate common tasks and interactions. These scripts are executed via the ``brownie run`` command.

See the :ref:`Brownie Scripts<scripts>` documentation for more information on Brownie scripts.

``tests/``
==========

The ``tests`` folder holds Python scripts used for testing a project. Brownie uses the `pytest <https://docs.pytest.org/en/latest/>`_ framework for unit testing.

See :ref:`Brownie Pytest<pytest>` documentation for more information on testing a project.
