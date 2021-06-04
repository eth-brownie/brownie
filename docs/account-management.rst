.. _local-accounts:

==================
Account Management
==================

When connecting to a remote network via a hosted node such as `Infura <https://infura.io/>`_, the :func:`Accounts <brownie.network.account.Accounts>` container will be empty. Before you can perform any transactions you must add a local account to Brownie.

When we use the term `local` it implies that the account exists locally on your system, as opposed to being available directly in the node. Local accounts are stored in encrypted JSON files known as `keystores`. If you want to learn more about keystore files, you can read If you want to understand the contents of your json file you can read `"What is an Ethereum keystore file?" <https://medium.com/@julien.maffre/what-is-an-ethereum-keystore-file-86c8c5917b97>`_ by Julien Maffre.

You can manage your locally available accounts via the commandline:

    ::

        $ brownie accounts

Generating a New Account
========================

To generate a new account using the command line:

    ::

        $ brownie accounts generate <id>

You will be asked to choose a password for the account. Brownie will then generate a random private key, and make the account available as ``<id>``.

Importing from a Private Key
============================

To add a new account via private key:

    ::

        $ brownie accounts new <id>

You will be asked to input the private key, and to choose a password. The account will then be available as ``<id>``.

Importing from a Keystore
=========================

You can import an existing JSON keystore into Brownie using the commandline:

    ::

        $ brownie accounts import <id> <path>

Once imported the account is available as ``<id>``.

Exporting a Keystore
====================

To export an existing account as a JSON keystore file:

    ::

        $ brownie accounts export <id> <path>

The exported account will be saved at ``<path>``.

Unlocking Accounts
==================

In order to access a local account from a script or console, you must first unlock it. This is done via the :func:`Accounts.load <Accounts.load>` method:

    .. code-block:: python

        >>> accounts
        []
        >>> accounts.load(id)
        >>> accounts.load('my_account')
        Enter the password for this account:
        <LocalAccount object '0xa9c2DD830DfFE8934fEb0A93BAbcb6e823e1FF05'>
        >>> accounts
        [<LocalAccount object '0xa9c2DD830DfFE8934fEb0A93BAbcb6e823e1FF05'>]

Once the account is unlocked it will be available for use within the :func:`Accounts <brownie.network.account.Accounts>` container.

Unlocking Accounts on Development Networks
==========================================

On a local or forked development network you can unlock and use any account, even if you don't have the corresponding private key.
To do so, add the account to the ``unlock`` setting in a project's :ref:`configuration file<config>`:

    .. code-block:: yaml

            networks:
                development:
                    cmd_settings:
                        unlock:
                            - 0x7E1E3334130355799F833ffec2D731BCa3E68aF6
                            - 0x0063046686E46Dc6F15918b61AE2B121458534a5

The unlocked accounts are automatically added to the :func:`Accounts <brownie.network.account.Accounts>` container.
Note that you might need to fund the unlocked accounts manually.

Using a Hardware Wallet
=======================

Brownie allows the use of hardware wallets via `Clef <https://geth.ethereum.org/docs/clef/tutorial>`_, an account management tool included within `Geth <https://geth.ethereum.org/>`_.

To use a hardware wallet in Brownie, start by `installing Geth <https://geth.ethereum.org/docs/install-and-build/installing-geth>`_. Once finished, type the following command and follow the on-screen prompts to set of Clef:

    ::

        clef init

Once Clef is configured, run Brownie in one command prompt and Clef in another. From within Brownie:

    .. code-block:: python

        >>> accounts.connect_to_clef()

Again, follow the prompts in Clef to unlock the accounts in Brownie. You can now use the unlocked accounts as you would any other account.  Note that you will have to authorize each transaction made with a :func:`ClefAccount <brownie.network.account.ClefAccount>` from within clef.
