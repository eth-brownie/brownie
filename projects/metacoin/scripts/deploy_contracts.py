
from brownie import *


def main():
    ConvertLib.deploy(accounts[0])
    MetaCoin.deploy(accounts[0])