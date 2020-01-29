.. _deploy:

=================
Deployment Basics
=================

Once your project is ready to be deployed to a persistent chain (such as the Etherem mainnet or a testnet), Brownie can be used to handle the deployments.

It is important to remember that blockchains are `permanent` and `immutable`. Once your project has been deployed there is no going back. For this reason, we highly recommend the following process when deploying to the mainnet:

    1. Create a deployment script
    2. Test the script on your local development environment
    3. Test the script again on one of the `public test networks <https://medium.com/compound-finance/the-beginners-guide-to-using-an-ethereum-test-network-95bbbc85fc1d>`_ and verify that it executed as intended
    4. Use the script to deploy your project to the mainnet

Once deployment is complete you may also :ref:`create an ethPM package<ethpm>` to simplify the process for other developers who wish to interact with your project.

Writing a Deployment Script
===========================

Deployment scripts function in the same way as any other :ref:`Brownie script<scripts>`, but there are a couple of things to keep in mind when writing one for a non-local network:

    1. Unless you are using your own node you will have to unlock a local account prior to deploying. This is handled within the script by calling :func:`Accounts.load <Accounts.load>`. If you have not yet added a local account to Brownie, read the documentation on :ref:`local account management<local-accounts>`.
    2. Most networks require that you to pay gas to miners. If no values are specified Brownie will calculate the gas price and limit automatically, but in some cases you may wish to manually declare these values.

Here is an small example script that unlocks a local account and uses it to deploy a ``Token`` contract.

.. code-block:: python

    from brownie import Token, accounts

    def main():
        acct = accounts.load('deployment_account')
        Token.deploy("My Real Token", "RLT", 18, "1000 ether", {'from': acct})

Running your Deployment Script
==============================

In order to execute your script on a non-local network, you must include the ``--network`` flag in the command line. For example, to connect to the ropsten network and run ``scripts/deploy.py``:

::

    $ brownie run deploy.py --network ropsten

Remember that transactions are not confirmed immediately on non-local networks. You will see a notification on the status of each transaction, however the script will take some time to complete.

See the documentation on :ref:`using non-local networks<nonlocal-networks>` for more information on how to define and connect to other networks.

.. _persistence:

Interacting with Deployed Contracts
===================================

Brownie saves information about contract deployments on non-local networks. Once a contract has been deployed, the generated :func:`Contract <brownie.network.contract.ProjectContract>` instance will still be available the next time you load Brownie.

The following actions will NOT remove locally stored deployment data:

    * Disconnecting and reconnecting to the same network
    * Closing and reloading a project
    * Exiting and reloading Brownie
    * Modifying a contract's source code - Brownie still retains the source for the deployed version

The following actions WILL remove locally stored deployment data:

    * Calling :func:`ContractContainer.remove <ContractContainer.remove>` will erase deployment information for the removed :func:`Contract <brownie.network.contract.ProjectContract>` instances.
    * Removing or renaming a contract source file within your project will cause Brownie to delete all deployment information for the removed contract.
    * Deleting the ``build/deployments/`` directory will erase all information about deployed contracts.

To restore a deleted :func:`Contract <brownie.network.contract.ProjectContract>` instance, or generate one for a deployment that was handled outside of Brownie, use the :func:`ContractContainer.at <ContractContainer.at>` method.
