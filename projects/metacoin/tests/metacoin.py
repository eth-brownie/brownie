from brownie import *

import scripts.deploy_contracts as deployer

def setup():
    global metaCoinInstance
    deployer.main()
    metaCoinInstance = MetaCoin[0]

def initial_balance():
    '''should put 10000 MetaCoin in the first account'''
    check.equal(
        metaCoinInstance.getBalance(accounts[0]),
        10000,
        "10000 wasn't in the first account"
    )

def library_fn():
    '''should call a function that depends on a linked library'''
    metaCoinBalance = metaCoinInstance.getBalance(accounts[0])
    metaCoinEthBalance = metaCoinInstance.getBalanceInEth(accounts[0])
    
    check.equal(
        metaCoinEthBalance,
        2 * metaCoinBalance,
        'Library function returned unexpected function, linkage may be broken'
    )

def transfer():
    '''should send coin correctly'''
    # Get initial balances of first and second account.
    accountOneStartingBalance = metaCoinInstance.getBalance(accounts[0])
    accountTwoStartingBalance = metaCoinInstance.getBalance(accounts[1])

    # Make transaction from first account to second.
    amount = 10;
    metaCoinInstance.sendCoin(accounts[1], amount, {'from': accounts[0]});

    # Get balances of first and second account after the transactions.
    accountOneEndingBalance = metaCoinInstance.getBalance(accounts[0])
    accountTwoEndingBalance = metaCoinInstance.getBalance(accounts[1])

    check.equal(
        accountOneEndingBalance,
        accountOneStartingBalance - amount,
        "Amount wasn't correctly taken from the sender"
    )
    check.equal(
        accountTwoEndingBalance,
        accountTwoStartingBalance + amount,
        "Amount wasn't correctly sent to the receiver"
    )