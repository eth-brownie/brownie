# Brownie

Brownie is a python framework for deploying, testing and interacting with Ethereum smart contracts.

## Dependencies

* [ganache-cli](https://github.com/trufflesuite/ganache-cli)
* [pip](https://pypi.org/project/pip/)
* [python3](https://www.python.org/downloads/release/python-368/) version 3.6 or greater, python3-dev, python3-tk

As Brownie relies on [py-solc-x](https://github.com/iamdefinitelyahuman/py-solc-x), you do not need solc installed locally but you must install all required [solc dependencies](https://solidity.readthedocs.io/en/latest/installing-solidity.html#binary-packages).

## Installation

You can install the latest release via pip:

```bash
$ pip install eth-brownie
```

Or clone the repository and use setuptools for the most up-to-date version:

```bash
$ python3 setup.py install
```

## Quick Usage

To set up the default folder and file structure for brownie use:

```bash
brownie init
```

From there, type `brownie` for basic usage information.

## Documentation

Brownie documentation is hosted at [Read the Docs](https://eth-brownie.readthedocs.io/en/latest/).

## Contributing

Help is always appreciated! In particular, Brownie needs work in the following areas before we can comfortably take it out of beta:

* Tests
* Travis or other CI
* More tests

Feel free to open an issue if you find a problem, or a pull request if you've solved an issue.

## License

This project is licensed under the [MIT license](LICENSE).
