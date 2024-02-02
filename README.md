# Brownie

[![Pypi Status](https://img.shields.io/pypi/v/eth-brownie.svg)](https://pypi.org/project/eth-brownie/) [![Docs Status](https://readthedocs.org/projects/eth-brownie/badge/?version=latest)](https://eth-brownie.readthedocs.io/en/stable/)

Brownie is a Python-based development and testing framework for smart contracts targeting the [Ethereum Virtual Machine](https://solidity.readthedocs.io/en/v0.6.0/introduction-to-smart-contracts.html#the-ethereum-virtual-machine).

**Brownie is no longer actively maintained**. Future releases may come sporadically - or never at all. Check out [Ape Framework](https://github.com/ApeWorX/ape) for all your python Ethereum development needs.

## Features

* Full support for [Solidity](https://github.com/ethereum/solidity) (`>=0.4.22`) and [Vyper](https://github.com/vyperlang/vyper) (`>=0.1.0-beta.16`)
* Contract testing via [`pytest`](https://github.com/pytest-dev/pytest), including trace-based coverage evaluation
* Property-based and stateful testing via [`hypothesis`](https://github.com/HypothesisWorks/hypothesis/tree/master/hypothesis-python)
* Powerful debugging tools, including python-style tracebacks and custom error strings
* Built-in console for quick project interaction

## Dependencies

* [python3](https://www.python.org/downloads/release/python-3910/) version 3.10 or greater, python3-dev
* [hardhat](https://github.com/NomicFoundation/hardhat) or [ganache](https://github.com/trufflesuite/ganache)

Tested with ganache version [7.9.2](https://github.com/trufflesuite/ganache/releases/tag/v7.0.2), however it is generally recommended to use hardhat because ganache has been sunsetted.

## Installation

### via `pipx`

The recommended way to install Brownie is via [`pipx`](https://github.com/pipxproject/pipx). pipx installs Brownie into a virtual environment and makes it available directly from the commandline. Once installed, you will never have to activate a virtual environment prior to using Brownie.

To install `pipx`:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

To install Brownie using `pipx`:

```bash
pipx install eth-brownie
```

To upgrade to the latest version:

```bash
pipx upgrade eth-brownie
```

To use lastest master or another branch as version:
```bash
pipx install git+https://github.com/eth-brownie/brownie.git@master
```

### via `pip`

You can install the latest release via [`pip`](https://pypi.org/project/pip/):

```bash
pip install eth-brownie
```

### via `setuptools`

You can clone the repository and use [`setuptools`](https://github.com/pypa/setuptools) for the most up-to-date version:

```bash
git clone https://github.com/eth-brownie/brownie.git
cd brownie
python3 setup.py install
```

### as a library

If you want to install brownie inside your own project (rather than as a standalone cli tool):

```bash
export BROWNIE_LIB=1
pip install eth-brownie
```

This loosens the pins on all dependencies. You'll want to make sure you have your own `requirements.txt` to make sure upgrades upstream don't surprise anyone.

### for development

There are extra tools that are helpful when developing:

```bash
git clone https://github.com/eth-brownie/brownie.git
cd brownie
python3 -m venv venv
./venv/bin/pip install wheel
./venv/bin/pip install -e . -r requirements-dev.txt
```

Upgrading the pinned versions of dependencies is easy:
```
./venv/bin/pip-compile --upgrade
./venv/bin/pip-compile --upgrade requirements-dev.in
./venv/bin/pip-compile --upgrade requirements-windows.in
```

Even small upgrades of patch versions have broken things in the past, so be sure to run all tests after upgrading things!

## Quick Usage

To initialize a new Brownie project, start by creating a new folder. From within that folder, type:

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
pip install -e . -r requirements-dev.txt
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

#### Attaching to dockerized RPC clients

You can also attach to a RPC client already running inside a docker container.

For example for running ganache-cli you could just startup the official ganache-cli docker image:

```bash
docker run -p 8545:8545 trufflesuite/ganache-cli
```

Then in another terminal on your host you could connect to it:

```bash
brownie console
```

If you have your RPC client bound to a specific hostname e.g. `ganache` you could create a separate brownie network for it:

```bash
brownie networks add Development dev cmd=ganache-cli host=http://ganache:8545
```

Then connect to it with:

```bash
brownie console --network dev
```

## Contributing

Help is always appreciated! Feel free to open an issue if you find a problem, or a pull request if you've solved an issue.

Please check out our [Contribution Guide](CONTRIBUTING.md) prior to opening a pull request, and join the Brownie [Gitter channel](https://gitter.im/eth-brownie/community) if you have any questions.

## License

This project is licensed under the [MIT license](LICENSE).
