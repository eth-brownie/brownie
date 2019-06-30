#!/usr/bin/python3

from brownie import accounts, project


def main():
    accounts[0].deploy(project.Token, "Test Token", "TEST", 18, "1000 ether")


def donothing(a):
    return a
