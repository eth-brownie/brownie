.. _install:

==================
Installing Brownie
==================

The recommended way to install Brownie is via `pipx <https://github.com/pipxproject/pipx>`_. Pipx is a tool to help you install and run end-user applications written in Python. It's roughly similar to macOS's ``brew``, JavaScript's ``npx``, and Linux's ``apt``.

``pipx`` installs Brownie into a virtual environment and makes it available directly from the commandline. Once installed, you will never have to activate a virtual environment prior to using Brownie.

``pipx`` does not ship with Python. If you have not used it before you will probably need to install it.

To install ``pipx``:

.. code-block:: bash

    python3 -m pip install --user pipx
    python3 -m pipx ensurepath

.. note::

    You may need to restart your terminal after installing ``pipx``.

To install Brownie using ``pipx``:

.. code-block:: bash

    pipx install eth-brownie

Once installation is complete, type ``brownie`` to verify that it worked:

.. code-block:: bash

    $ brownie
    Brownie - Python development framework for Ethereum

    Usage:  brownie <command> [<args>...] [options <args>]


Other Installation Methods
==========================

You can also install Brownie via ``pip``, or clone the repository and use ``setuptools``. If you install via one of these methods, we highly recommend using ``venv`` and installing into a `virtual environment <https://docs.python.org/3/library/venv.html>`_.

To install via ``pip``:

.. code-block:: bash

    pip install eth-brownie

To clone the `github repository <https://github.com/eth-brownie/brownie>`_ and install via ``setuptools``:

.. code-block:: bash

    git clone https://github.com/eth-brownie/brownie.git
    cd brownie
    python3 setup.py install

Dependencies
============

Brownie has the following dependencies:

* `python3 <https://www.python.org/downloads/release/python-368/>`_ version 3.6 or greater, python3-dev
* `ganache-cli <https://github.com/trufflesuite/ganache-cli>`_ - tested with version `6.12.2 <https://github.com/trufflesuite/ganache-cli/releases/tag/v6.12.2>`_

.. _install-tk:

Tkinter
-------

:ref:`The Brownie GUI<gui>` is built using the `Tk GUI toolkit <https://tcl.tk/>`_. Both Tk and `tkinter <https://docs.python.org/3.8/library/tkinter.html>`_ are available on most Unix platforms, as well as on Windows systems.

Tk is not a strict dependency for Brownie. However, if it is not installed on your system you will receive an error when attempting to load the GUI.

You can use the following command to check that Tk has been correctly installed:

.. code-block:: bash

    python -m tkinter

This should open a simple window and display the installed version number.

For installation instructions read `Installing TK <https://tkdocs.com/tutorial/install.html>`_ within the TK Documentation.

Using Brownie with Hardhat
==========================

`Hardhat <https://github.com/nomiclabs/hardhat>`_ is an Ethereum development environment with similar functionality to Brownie. Hardhat includes the `Hardhat Network <https://hardhat.org/hardhat-network/>`_, a local development node similar to `Ganache <https://github.com/trufflesuite/ganache-cli>`_. The Hardhat Network may be used as an alternative to Ganache within Brownie.

    .. note::

        Hardhat integration within Brownie is a new feature and still under development. Functionality should be on-par with Ganache, however there may still be bugs. Please open an issue on Github if you run into any inconsistencies or missing functionality.

To use the Hardhat network with Brownie you must first install Hardhat. This can either be done in the root directory of each Brownie project, or once in your home directory:

    .. code-block:: bash

        npm install --save-dev hardhat

See the `Hardhat documentation <https://hardhat.org/getting-started/#installation>`_ for more information on installing Hardhat.

Once installed, include the ``--network hardhat`` flag to run Brownie with Hardhat. For example, to launch the console:

    .. code-block:: bash

        brownie console --network hardhat

The first time you use Hardhat within a Brownie project, a ``hardhat.config.js`` `configuration file <https://hardhat.org/config/>`_ is generated. You should not modify any of the settings within this file as they are required for compatibility.

If you have updated your brownie version from older versions, hardhat networks will be missing. You have to update ``~/.brownie/network-config.yaml``. It can be updated using the one `here <https://github.com/eth-brownie/brownie/blob/master/brownie/data/network-config.yaml>`_


Using Brownie with Anvil
==========================

`Anvil <https://github.com/foundry-rs/foundry/tree/master/crates/anvil>`_ is a blazing-fast local testnet node implementation in Rust. Anvil may be used as an alternative to Ganache within Brownie.

To use Anvil with Brownie, you must first `follow their steps to install Anvil <https://github.com/foundry-rs/foundry/tree/master/crates/anvil#installation>`_.

Once installed, include the ``--network anvil`` or ``--network anvil-fork`` flag to run Brownie with Anvil. For example, to launch the console:

    .. code-block:: bash

        brownie console --network anvil

If you have updated your brownie version from older versions, anvil networks will be missing. You have to update ``~/.brownie/network-config.yaml``. It can be updated using the one `here <https://github.com/eth-brownie/brownie/blob/master/brownie/data/network-config.yaml>`_
