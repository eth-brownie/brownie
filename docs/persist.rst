.. _persist:

=======================
Persistent Environments
=======================

When using non-local environments, you can enable persistence by adding ``"persist": true`` in the config file. See :ref:`config` for information on how edit the config file.

When enabled, persistence will maintain:

* ``accounts``: If you are using Infura or another public node, you can save any accounts you've added with ``accounts.add`` so you don't have to re-enter the private keys.
* ``ContractDeployer``: Any contracts you have deployed or made reference to with ``.at`` will be available in their deployer container.

The first time Brownie is run on a network with persistence enabled, it will ask you to set a password. The persistent data is then encrypted and stored at ``build/networks/[network].json``. The next time you load Brownie you will be asked to enter the password. You can instead enter CTRL-C to use the network without persistence.

You can use the ``reset`` command in the console to forget the addresses of deployed contracts on the active network. Local accounts that were added with ``accounts.add`` will not not be removed, they must be deleted manually from the ``accounts`` container.

You can also delete the ``build/networks/`` folder to erase all persistent data.
