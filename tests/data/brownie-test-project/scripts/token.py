#!/usr/bin/python3

from brownie import *


def main():
    accounts[0].deploy(BrownieTester, True)


def donothing(a):
    return a
