.. _init:

======================
Creating a New Project
======================

The first step to using Brownie is to initialize a new project. This can be done in two ways:

1. Create an empty project using ``brownie init``.
2. Create a project from an existing template using ``brownie bake``.

Creating an Empty Project
=========================

To initialize an empty project, start by creating a new folder. From within that folder, type:

::

    $ brownie init

An empty :ref:`project structure<structure>` is created within the folder.

To initialize an empty project inside a new empty or existing folder type:

::

    $ brownie init -f

Creating a Project from a Template
==================================

You can initialize "`Brownie mixes <https://github.com/brownie-mix>`_", simple templates to build your project upon. For many examples within the Brownie documentation we will use the `token <https://github.com/brownie-mix/token-mix>`_ mix, which is a very basic ERC-20 implementation.

Mixes are automatically created within a subfolder of their name. To initialize the ``token`` mix:

::

    $ brownie bake token

This creates a new folder ``token/`` and deploys the project inside it.

React Template
--------------
`React-Mix <https://github.com/brownie-mix/react-mix>`_ is a bare-bones implementation of `Create React App <https://create-react-app.dev/>`_ configured to work with Brownie. You can use it as a starting point for building your own React frontend for your dApp.

To initialize from this mix:

::

    $ brownie bake react

See the `React-Mix repo <https://github.com/brownie-mix/react-mix>`_ for more information on how to use React with Brownie.

Continuous Integration Template
-------------------------------

`Github-Actions-Mix <https://github.com/brownie-mix/github-actions-mix>`_ is a template preconfigured for use with `Github Actions <https://github.com/features/actions>`_ continuous integration, as well as other useful tools.

To initialize from this mix:

::

    $ brownie bake github-actions

See the `Github-Actions-Mix repo <https://github.com/brownie-mix/github-actions-mix>`_ for a detailed explanation of how to configure and use the tools within this template.
