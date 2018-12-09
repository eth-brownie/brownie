
==========================
Initializing a New Project
==========================

The first step to using Brownie is to initialize a new project. To do this, create a new empty folder and then type:

::

    $ brownie init

This will create the following project structure within the folder:

* ``build``: Directory for compiled conntracts and network data
* ``contracts/``: Directory for solidity contracts
* ``deployments/``: Directory for deployment scripts
* ``environments/``: Directory for persistent environment data files
* ``test/``: Directory for test scripts
* ``brownie-config.json``: Configuration file for the project

You can also initialize already existing projects. This is useful if you wish to define templates for common starting points on new projects. To initialize the 'token' project, which is provided as a demo:

::

    $ brownie init token

This will create a new folder ``token/`` and deploy the project inside it.
