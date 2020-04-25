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

To clone the `github repository <https://github.com/iamdefinitelyahuman/brownie>`_ and install via ``setuptools``:

.. code-block:: bash

    git clone https://github.com/iamdefinitelyahuman/brownie.git
    cd brownie
    python3 setup.py install

Dependencies
============

Brownie has the following dependencies:

* `python3 <https://www.python.org/downloads/release/python-368/>`_ version 3.6 or greater, python3-dev
* `ganache-cli <https://github.com/trufflesuite/ganache-cli>`_ - tested with version `6.8.2 <https://github.com/trufflesuite/ganache-cli/releases/tag/v6.8.2>`_

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
