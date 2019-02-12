# Brownie

Brownie is a python framework for deploying, testing and interacting with ethereum smart contracts.

## Dependencies

* [ganache-cli](https://github.com/trufflesuite/ganache-cli)
* [git](https://git-scm.com/)
* [pip](https://pypi.org/project/pip/)
* [python3.6](https://www.python.org/downloads/release/python-368/), python3.6-dev, python3.6-venv

> There is an issue in ganache-cli 6.3.0 relating to ``evm_revert`` that may cause tests to unexpectedly fail. At present, it is recommended to use version [6.2.5](https://github.com/trufflesuite/ganache-cli/releases/tag/v6.2.5).

As brownie relies on [py-solc-x](https://github.com/iamdefinitelyahuman/py-solc-x), you do not need solc installed locally but you must install all required [solc dependencies](https://solidity.readthedocs.io/en/latest/installing-solidity.html#binary-packages).

You may also wish to install [opview](https://github.com/HyperLink-Technology/opview) for test coverage visualization.

## Installation

Ubuntu:

```bash
curl https://raw.githubusercontent.com/HyperLink-Technology/brownie/master/brownie-install.sh | sh
```

## Quick Usage

To set up the default folder and file structure for brownie use:

```bash
brownie init
```

From there, type `brownie` for basic usage information.

## Documentation

Brownie documentation is hosted at [Read the Docs](https://eth-brownie.readthedocs.io/en/latest/).

## Development

This project is still in development and should be considered a beta. Comments, questions, criticisms and pull requests are welcomed.

## License

This project is licensed under the [MIT license](LICENSE).