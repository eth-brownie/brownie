.. _quickstart:

==========
Quickstart
==========

This page will walk you through the basics of using Brownie.

Initializing a New Project
==========================

The first step to using Brownie is to initialize a new project. To do this, create a new empty folder and then type:

::

    brownie init

This will create the following project structure within the folder:

* ``contracts/``: Directory for solidity contracts
* ``deployments/``: Directory for deployment scripts
* ``environments/``: Directory for persistent environment data files
* ``test/``: Directory for test scripts
* ``brownie-config.json``: Configuration file for the project

You can also initialize already existing projects. For the purposes of this document, we will use the ``token`` project, which is a very basic ERC-20 implementation:

::

    brownie init token

This will create a new folder ``token/`` and deploy the project inside it.

