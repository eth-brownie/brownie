#!/usr/bin/python3

registry = set()

active = {
    'rpc': None,
    'web3': None
}

def add(obj):
    registry.add(obj)

def remove(obj):
    registry.discard(obj)
    
def revert():
    for obj in registry:
        obj._notify()

def reset():
    for obj in registry:
        obj._notify_reset()

def set_web3(web3):
    for obj in registry:
        obj.web3 = web3