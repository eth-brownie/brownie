.. _api-project:

===========
Project API
===========

``brownie.project``
===================

The ``project`` package contains classes and methods for creating, loading, compiling and interacting with Brownie projects.

``brownie.project.compiler``
============================

Tne ``compiler`` module contains methods for compiling contracts and formatting the compiled data.

.. py:method:: compile_source(source)

    Compiles the given string and returns a list of ContractContainer instances.

    .. code-block:: python

        >>> container = compile_source('''pragma solidity 0.4.25;

        contract SimpleTest {

          string public name;

          constructor (string _name) public {
            name = _name;
          }
        }'''

        [<ContractContainer object 'SimpleTest'>]
        >>> container[0]
        []

``brownie.project._build``
==========================

The ``_build`` module contains classes and methods used internally by Brownie to interact with files in a project's ``build`` folder.

``brownie.project._sha_compare``
================================

The ``_sha_compare`` module contains methods for generating and comparing hashes that are used to determine if contracts should be recompiled or tests should be re-run.
