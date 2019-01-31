#!/usr/bin/python3

from brownie import *

def deploy():
    accounts[0].deploy(Token, "Test Token", "TEST", 18, "1000 ether")