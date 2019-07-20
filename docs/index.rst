=======
Brownie
=======

Brownie is a Python framework for Ethereum smart contract testing, interaction and deployment.

.. note::

    All code starting with ``$`` is meant to be run on your terminal. Code starting with ``>>>`` is meant to run inside the Brownie console.

.. note::

    This project relies heavily upon ``web3.py`` and the documentation assumes a basic familiarity with it. You may wish to view the `Web3.py docs <https://web3py.readthedocs.io/en/stable/index.html>`__ if you have not used it previously.

Brownie has several uses:

* **Testing**: Unit test your project with ``pytest``, and evaluate test coverage through stack trace analysis. We make *no promises*.
* **Debugging**: Get detailed information when a transaction reverts, to help you locate and solve the issue quickly.
* **Interaction**: Write scripts or use the console to interact with your contracts on the main-net, or for quick testing in a local environment.
* **Deployment**: Automate the deployment of many contracts onto the blockchain, and any transactions needed to initialize or integrate the contracts.

