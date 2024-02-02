.. _deploy:

=================
Deployment Basics
=================

Once your project is ready to be deployed to a persistent chain (such as the Ethereum mainnet or a testnet), Brownie can be used to handle the deployments.

It is important to remember that blockchains are `permanent` and `immutable`. Once your project has been deployed there is no going back. For this reason, we highly recommend the following process when deploying to the mainnet:

    1. Create a deployment script
    2. Test the script on your local development environment
    3. Test the script again on one of the `public test networks <https://medium.com/compound-finance/the-beginners-guide-to-using-an-ethereum-test-network-95bbbc85fc1d>`_ and verify that it executed as intended
    4. Use the script to deploy your project to the mainnet

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
        Token.deploy("My Real Token", "RLT", 18, 1e28, {'from': acct})

Running your Deployment Script
==============================

In order to execute your script in a live environment, you must include the ``--network`` flag in the command line. For example, to connect to the ropsten network and run ``scripts/deploy.py``:

::

    $ brownie run deploy.py --network ropsten

Remember that transactions are not confirmed immediately on live networks. You will see a notification on the status of each transaction, however the script will take some time to complete.

See the documentation on :ref:`network management<network-management>` for more information on how to define and connect to live networks.

.. _persistence:

The Deployment Map
==================

Brownie will maintain a ``map.json`` file in your ``build/deployment/`` folder that lists all deployed contracts on live networks, sorted by chain and contract name.

.. code-block:: json

    {
      "1": {
        "SolidityStorage": [
          "0x73B74F5f1d1f7A00d8c33bFbD09744eD90220D12",
          "0x189a7fBB0038D4b55Bd03840be0B0a38De034089"
        ],
        "VyperStorage": [
          "0xF104A50668c3b1026E8f9B0d9D404faF8E42e642"
        ]
      }
    }

The list for each contract is sorted by the block number of the deployment with the most recent deployment first.

Interacting with Deployed Contracts
===================================

Brownie saves information about contract deployments on live networks. Once a contract has been deployed, the generated :func:`ProjectContract <brownie.network.contract.ProjectContract>` instance will still be available in future Brownie sessions.

The following actions will NOT remove locally stored deployment data:

    * Disconnecting and reconnecting to the same network
    * Closing and reloading a project
    * Exiting and reloading Brownie
    * Modifying a contract's source code - Brownie still retains the source for the deployed version

The following actions WILL remove locally stored deployment data within your project:

    * Calling :func:`ContractContainer.remove <ContractContainer.remove>` will erase deployment information for the removed :func:`ProjectContract <brownie.network.contract.ProjectContract>` instances.
    * Removing or renaming a contract source file within your project will cause Brownie to delete all deployment information for the removed contract.
    * Deleting the ``build/deployments/`` directory will erase all information about deployed contracts.

To restore a deleted :func:`ProjectContract <brownie.network.contract.ProjectContract>` instance, or generate one for a deployment that was handled outside of Brownie, use the :func:`ContractContainer.at <ContractContainer.at>` method.

Verifying Deployment Source Code
==========================================

Brownie features automatic source code verification for solidity contracts on all networks supported by etherscan. To verify a contract while deploying it, add the ``publish_source=True`` argument:

.. code-block:: python

    acct = accounts.load('deployment_account')
    Token.deploy("My Real Token", "RLT", 18, 1e28, {'from': acct}, publish_source=True)

Verifying already deployed contracts is also possible as long as you set the identical compiler settings:

.. code-block:: python

    token = Token.at("0x114A107C1931de1d5023594B14fc19d077FC4dfD")
    Token.publish_source(token)


.. warning::

        Make sure all your source files use the same compiler version, otherwise the verification will fail.

Saving Deployments on Development Networks
==========================================

If you need deployment artifacts on a development network, set :attr:`dev_deployment_artifacts` to ``true`` in the in the project's ``brownie-config.yaml`` file.

These temporary deployment artifacts and the corresponding entries in :ref:`the deployment map<persistence>`  will be removed whenever you (re-) load a project or connect, disconnect, revert or reset your local network.

If you use a development network that is not started by brownie - for example an external instance of ganache - the deployment artifacts will not be deleted when disconnecting from that network.
However, the network will be reset and the deployment artifacts deleted when you connect to such a network with brownie.
