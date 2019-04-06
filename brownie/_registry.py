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
    for obj in [i for i in registry if hasattr(i, '_notify_revert')]:
        obj._notify_revert()

def reset(web3):
    for obj in [i for i in registry if hasattr(i, 'web3')]:
        obj.web3 = web3
    for obj in [i for i in registry if hasattr(i, '_notify_reset')]:
        obj._notify_reset()