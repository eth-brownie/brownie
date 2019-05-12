==========================
Initializing a New Project
==========================

The first step to using Brownie is to initialize a new project. To do this, create a new empty folder and then type:

::

    $ brownie init

This will create the following project structure within the folder:

* ``build/``: Compiled contracts and test data
* ``contracts/``: Contract source code
* ``reports/``: JSON report files for use in the :ref:`coverage-gui`
* ``scripts/``: Scripts for deployment and interaction
* ``tests/``: Scripts for testing your project
* ``brownie-config.json``: Configuration file for the project

You can also initialize "`Brownie mixes <https://github.com/brownie-mix>`__", simple templates to build your project upon. For many examples within the Brownie documentation we will use the `token <https://github.com/brownie-mix/token-mix>`__ mix, which is a very basic ERC-20 implementation:

::

    $ brownie bake token

This creates a new folder ``token/`` and deploys the project inside it.
