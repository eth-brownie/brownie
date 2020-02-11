# Brownie

[![Pypi Status](https://img.shields.io/pypi/v/eth-brownie.svg)](https://pypi.org/project/eth-brownie/) [![Build Status](https://travis-ci.com/iamdefinitelyahuman/brownie.svg?branch=master)](https://travis-ci.com/iamdefinitelyahuman/brownie) [![Docs Status](https://readthedocs.org/projects/eth-brownie/badge/?version=latest)](https://eth-brownie.readthedocs.io/en/latest/) [![Coverage Status](https://coveralls.io/repos/github/iamdefinitelyahuman/brownie/badge.svg?branch=master)](https://coveralls.io/github/iamdefinitelyahuman/brownie?branch=master)

Brownie is a Python-based development and testing framework for smart contracts targeting the [Ethereum Virtual Machine](https://solidity.readthedocs.io/en/v0.6.0/introduction-to-smart-contracts.html#the-ethereum-virtual-machine).

## Features

* Full support for [Solidity](https://github.com/ethereum/solidity) (`>=0.4.22`) and [Vyper](https://github.com/vyperlang/vyper) (`0.1.0-b16`)
* Contract testing via [`pytest`](https://github.com/pytest-dev/pytest), including trace-based coverage evaluation
* Property-based and stateful testing via [`hypothesis`](https://github.com/HypothesisWorks/hypothesis/tree/master/hypothesis-python)
* Powerful debugging tools, including python-style tracebacks and custom error strings
* Built-in console for quick project interaction
* Support for [ethPM](https://www.ethpm.com) packages

## Dependencies

* [ganache-cli](https://github.com/trufflesuite/ganache-cli) - tested with version [6.8.2](https://github.com/trufflesuite/ganache-cli/releases/tag/v6.8.2)
* [pip](https://pypi.org/project/pip/)
* [python3](https://www.python.org/downloads/release/python-368/) version 3.6 or greater, python3-dev

As Brownie relies on [`py-solc-x`](https://github.com/iamdefinitelyahuman/py-solc-x), you do not need solc installed locally but you must install all required [solc dependencies](https://solidity.readthedocs.io/en/latest/installing-solidity.html#binary-packages).

## Installation

You can install the latest release via [`pip`](https://pypi.org/project/pip/):

```bash
pip install eth-brownie
```

Or clone the repository and use [`setuptools`](https://github.com/pypa/setuptools) for the most up-to-date version:

```bash
python setup.py install
```

## Quick Usage

To set up the default folder and file structure for Brownie use:

```bash
brownie init
```

Next, type `brownie --help` for basic usage information.

## Documentation and Support

Brownie documentation is hosted at [Read the Docs](https://eth-brownie.readthedocs.io/en/latest/).

If you have any questions about how to use Brownie, feel free to ask on [Ethereum StackExchange](https://ethereum.stackexchange.com/) or join us on [Gitter](https://gitter.im/eth-brownie/community).

## Testing

To run the tests, first install the developer dependencies:

```bash
pip install -r requirements-dev.txt
```

Then use [`tox`](https://github.com/tox-dev/tox) to run the complete suite against the full set of build targets, or [`pytest`](https://github.com/pytest-dev/pytest) to run tests against a specific version of Python. If you are using [`pytest`](https://github.com/pytest-dev/pytest) you must include the `-p no:pytest-brownie` flag to prevent it from loading the Brownie plugin.

### Using Docker

You can use a sandbox container provided in the [`docker-compose.yml`](docker-compose.yml) file for testing inside a Docker environment.

This container provides everything you need to test using a Python 3.6 interpreter.

Start the test environment:

```bash
docker-compose up -d
```

To open a session to the container:

```bash
docker-compose exec sandbox bash
```

To run arbitrary commands, use the `bash -c` prefix.

```bash
docker-compose exec sandbox bash -c ''
```

For example, to run the tests in `brownie/tests/test_format_input.py`:

```bash
docker-compose exec sandbox bash -c 'python -m pytest tests/convert/test_format_input.py'
```

## Contributing

Help is always appreciated! Feel free to open an issue if you find a problem, or a pull request if you've solved an issue.

Please check out our [Contribution Guide](CONTRIBUTING.md) prior to opening a pull request, and join the Brownie [Gitter channel](https://gitter.im/eth-brownie/community) if you have any questions.

## License

This project is licensed under the [MIT license](LICENSE).
