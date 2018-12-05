===================
Deploying A Project
===================

To deploy a project:

::

    brownie deploy [script]

Deployment scripts are stored in the ``deploy/`` folder. Each deployment script should contain a single method named ``deploy`` that takes no arguments. A deployment script will look something like this:

.. literalinclude:: ../projects/token/deployments/token.py
    :linenos:
    :language: python
    :lines: 3-

This deploys the ``Token`` contract from ``contracts/Token.sol`` using ``web3.eth.accounts[0]``.

For available classes and methods when writing a deployment script, see the :ref:`api` documentation.
