.. _persist:

=======================
Persistent Environments
=======================

When using non-local environments, you can enable persistence by adding ``"persist": true`` in the config file. See :ref:`config` for information on how edit the config file.

When enabled, persistence will maintain:

* ``accounts``: If you are using Infura, you can save any accounts you've added with ``accounts.add`` so you don't have to re-input the private keys.
* ``ContractDeployer``: Any contracts you have deployed or made reference to with ``.at`` will be available in their deployer container.

The first time Brownie is run on a network with persistence enabled, it will ask you to set a password. The persistent data is then encrypted and stored at ``environments/[network].evn``. The next time you load Brownie you will be asked to enter the password. You can instead enter CTRL-C to use the network without persistence.

Make sure to include ``environments/`` in your ``.gitignore``.
