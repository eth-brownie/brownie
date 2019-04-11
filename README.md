# Brownie

Brownie is a python framework for deploying, testing and interacting with Ethereum smart contracts.

## Dependencies

* [ganache-cli](https://github.com/trufflesuite/ganache-cli)
* [pip](https://pypi.org/project/pip/)
* [python3](https://www.python.org/downloads/release/python-368/) version 3.6 or greater, python3-dev, python3-venv

As brownie relies on [py-solc-x](https://github.com/iamdefinitelyahuman/py-solc-x), you do not need solc installed locally but you must install all required [solc dependencies](https://solidity.readthedocs.io/en/latest/installing-solidity.html#binary-packages).

You may also wish to install [opview](https://github.com/HyperLink-Technology/opview) for test coverage visualization.

## Installation

```bash
pip install eth-brownie
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
* Improving the documentation
* More tests
* Travis or other CI

Feel free to open an issue if you find a problem, or a pull request if you've solved an issue.

## License

This project is licensed under the [MIT license](LICENSE).
