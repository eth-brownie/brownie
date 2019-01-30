.. _install:

==================
Installing Brownie
==================

**Ubuntu**

This installs brownie at ``/usr/local/lib/brownie/`` and creates a virtual environment with all the required packages.

::

    $ curl https://raw.githubusercontent.com/iamdefinitelyahuman/brownie/master/brownie-install.sh | sh


Dependencies
============

Brownie has the following dependencies:

* `pip <https://pypi.org/project/pip/>`__
* `python3.6 <https://www.python.org/downloads/release/python-368/>`__ , python3.6-dev, python3.6-venv

As brownie relies on `py-solc-x <https://github.com/iamdefinitelyahuman/py-solc-x>`__, you do not need solc installed locally but you must install all required `solc dependencies <https://solidity.readthedocs.io/en/latest/installing-solidity.html#binary-packages>`__.

If you wish to run a local test environment you must also install an Ethereum client which supports the standard JSON RPC API. By default, Brownie is set to work with `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__, but you can easily change this by editing the ``brownie-config.json`` file in your project.

You may also wish to install `opview <https://github.com/iamdefinitelyahuman/opview>`__ for test coverage visualization.
