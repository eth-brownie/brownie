.. _install:

==================
Installing Brownie
==================

**Ubuntu**

This installs brownie at ``/usr/local/lib/brownie/``, creates a virtual environment with all the required packages, and places a bash script in ``/usr/local/bin`` so you can run brownie in any folder.

::

    $ curl https://raw.githubusercontent.com/HyperLink-Technology/brownie/master/brownie-install.sh | sh


**Docker**

A dockerfile is provided within the github repo. To build the image:

::

    $ docker build https://github.com/HyperLink-Technology/brownie.git -t brownie:1

You can then run brownie with:

::

    $ docker run -v $PWD:/usr/src brownie brownie


Dependencies
============

Brownie has the following dependencies:

* `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__
* `git <https://git-scm.com/>`__
* `pip <https://pypi.org/project/pip/>`__
* `python3.6 <https://www.python.org/downloads/release/python-368/>`__ , python3.6-dev, python3.6-venv

.. warning:: There is an issue in ganache-cli 6.3.0 relating to ``evm_revert`` that may cause tests to unexpectedly fail. At present, it is recommended to use version `6.2.5 <https://github.com/trufflesuite/ganache-cli/releases/tag/v6.2.5>`__.

As brownie relies on `py-solc-x <https://github.com/iamdefinitelyahuman/py-solc-x>`__, you do not need solc installed locally but you must install all required `solc dependencies <https://solidity.readthedocs.io/en/latest/installing-solidity.html#binary-packages>`__.

You may also wish to install `opview <https://github.com/HyperLink-Technology/opview>`__ for test coverage visualization.
