# Brownie

[![Pypi Status](https://img.shields.io/pypi/v/eth-brownie.svg)](https://pypi.org/project/eth-brownie/) [![Build Status](https://img.shields.io/travis/com/iamdefinitelyahuman/brownie.svg)](https://travis-ci.com/iamdefinitelyahuman/brownie) [![Docs Status](https://readthedocs.org/projects/eth-brownie/badge/?version=latest)](https://eth-brownie.readthedocs.io/en/latest/) [![Coverage Status](https://coveralls.io/repos/github/iamdefinitelyahuman/brownie/badge.svg?branch=master)](https://coveralls.io/github/iamdefinitelyahuman/brownie?branch=master)

Brownie is a Python framework for deploying, testing and interacting with Ethereum smart contracts.

## Dependencies

* [ganache-cli](https://github.com/trufflesuite/ganache-cli)
* [pip](https://pypi.org/project/pip/)
* [python3](https://www.python.org/downloads/release/python-368/) version 3.6 or greater, python3-dev, python3-tk

As Brownie relies on [py-solc-x](https://github.com/iamdefinitelyahuman/py-solc-x), you do not need solc installed locally but you must install all required [solc dependencies](https://solidity.readthedocs.io/en/latest/installing-solidity.html#binary-packages).

## Installation

You can install the latest release via ``pip``:

```bash
$ pip install eth-brownie
```

Or clone the repository and use ``setuptools`` for the most up-to-date version:

```bash
$ python3 setup.py install
```

## Quick Usage

To set up the default folder and file structure for Brownie use:

```bash
$ brownie init
```

Next, type ``brownie --help`` for basic usage information.

## Documentation

Brownie documentation is hosted at [Read the Docs](https://eth-brownie.readthedocs.io/en/latest/).

## Testing

To run the tests, first install the developer dependencies:

```bash
$ pip install -r requirements-dev.txt
```

Then use ``tox`` to run the complete suite against the full set of build targets, or ``pytest`` to run tests against a specific version of Python. If you are using ``pytest`` you must include the ``-p no:pytest-brownie`` flag to prevent it from loading the Brownie plugin.

## Contributing

Help is always appreciated! Feel free to open an issue if you find a problem, or a pull request if you've solved an issue.

## License

This project is licensed under the [MIT license](LICENSE).
