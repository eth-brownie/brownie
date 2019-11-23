#!/usr/bin/python3

from brownie import *


def main():
    accounts[0].deploy(BrownieTester, True)


def args_method(arg):
    return arg


def kwargs_method(first=None, second=None):
    return first, second


def do_nothing():
    return "potato"
