.. _hypothesis:

=======================
Managing Local Accounts
=======================

TODO

Brownie will automatically load any unlocked accounts returned by a node. If you are using your own private node, you will be able to access your accounts in the same way you would in a local environment.

In order to use accounts when connected to a hosted node, you must make them available locally.  This is done via ``brownie accounts`` in the command line:

::

    $ brownie accounts --help
    Brownie v1.3.2 - Python development framework for Ethereum

    Usage: brownie accounts <command> [<arguments> ...] [options]

    Commands:
    list                             List available accounts
    new <id>                         Add a new account by entering a private key
    generate <id>                    Add a new account with a random private key
    import <id> <path>               Import a new account via a keystore file
    export <id> <path>               Export an existing account keystore file
    password <id>                    Change the password for an account
    delete <id>                      Delete an account

After an account has been added, it can be accessed in the console or a script through :ref:`Accounts.load <api-network-accounts-load>`.
