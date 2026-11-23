.. _package-manager:

=======================
Brownie Package Manager
=======================

Brownie allows you to install other projects as packages. Some benefits of packages include:

* Easily importing and building upon code ideas written by others
* Reducing duplicated code between projects
* Writing unit tests that verify interactions between your project and another project

The Brownie package manager is available from the commandline:

.. code-block:: bash

    $ brownie pm

Installing a Package
====================

Brownie supports package installation from Github.

Installing from Github
----------------------

The easiest way to install a package is from a Github repository. Brownie considers a Github repository to be a package if meets the following criteria:

    * The repository must have one or more tagged versions.
    * The repository must include a ``contracts/`` folder containing one or more Solidity or Vyper source files.

A repository does not have to implement Brownie in order to function as a package. Many popular projects using frameworks such as Truffle or Embark can be added as Brownie packages.

To install a package from Github you must use a package ID. A package ID is comprised of the name of an organization, a repository, and a version tag. Package IDs are not case sensitive.

.. code-block:: bash

    [ORGANIZATION]/[REPOSITORY]@[VERSION]

It is possible to install from a private Github repository using an API access token like a `personal access token <https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token>`_.
This can be provided to Brownie via the ``GITHUB_TOKEN`` environment variable in the form of ``username:ghp_token_secret``.
See also https://docs.github.com/en/rest/overview/other-authentication-methods#basic-authentication.

.. note::

    Be careful to avoid exposing your API token in your command history or otherwise, and don't grant it more permissions than necessary!
    In this case **repo** permissions should be sufficient.


Examples
********

To install `OpenZeppelin contracts <https://github.com/OpenZeppelin/openzeppelin-contracts>`_ version ``3.0.0``:

.. code-block:: bash

    $ brownie pm install OpenZeppelin/openzeppelin-contracts@3.0.0

To install `AragonOS <https://github.com/aragon/aragonOS>`_ version ``4.0.0``:

.. code-block:: bash

    $ brownie pm install aragon/aragonos@4.0.0

Working with Packages
=====================

Viewing Installed Packages
--------------------------

Use ``brownie pm list`` to view currently installed packages. After installing all of the examples given above, the output looks something like this:

.. code-block:: bash

    $ brownie pm list
    Brownie - Python development framework for Ethereum

    The following packages are currently installed:

    OpenZeppelin
    └─OpenZeppelin/openzeppelin-contracts@3.0.0

    aragon
    └─aragon/aragonOS@4.0.0

    zeppelin.snakecharmers.eth
    └─zeppelin.snakecharmers.eth/access@1.0.0

    defi.snakecharmers.eth
    └─defi.snakecharmers.eth/compound@1.1.0

Cloning a Package
-------------------

Use ``brownie pm clone [path]`` to copy the contents of a package into another folder. The package will be cloned to the current directory if [path] is omitted. This is useful for exploring the filestructure of a package, or when you wish to build a project on top of an existing package.

To copy the Aragon package to the current folder:

.. code-block:: bash

    $ brownie pm clone aragon/aragonOS@4.0.0

Using Packages in your Project
==============================

Importing Sources from a Package
--------------------------------

You can import sources from an installed package in the same way that you would a source within your project. The root path is based on the name of the package and can be obtained via ``brownie pm list``.

For example, to import ``SafeMath`` from OpenZeppelin contracts:

.. code-block:: solidity

    import "OpenZeppelin/openzeppelin-contracts@3.0.0/contracts/math/SafeMath.sol";

You can modify the import path with the ``remappings`` field in your project configuration file. See :ref:`Remapping Installed Packages <compile-remap-packages>` for more information.

Using Packages in Tests
-----------------------

The ``pm`` fixture provides access to installed packages during testing. It returns a :func:`Project <brownie.project.main.Project>` object when called with a project ID:

.. code-block:: python

    def test_with_compound_token(pm):
        compound = pm('defi.snakecharmers.eth/compound@1.1.0').CToken

See the :ref:`unit test documentation<pytest-other-projects>` for more detailed information.

.. _package-manager-deps:

Declaring Project Dependencies
------------------------------

Dependencies are declared by adding a ``dependencies`` field to your project :ref:`configuration file <config>`:

.. code-block:: yaml

    dependencies:
        - aragon/aragonOS@4.0.0
        - defi.snakecharmers.eth/compound@1.1.0

Brownie attempts to install any listed dependencies prior to compiling a project. This is useful when your project may be used outside of your local environment.
