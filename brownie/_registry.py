#!/usr/bin/python3

registry = set()


def add(obj):
    registry.add(obj)

def remove(obj):
    registry.discard(obj)
    
def revert():
    for obj in [i for i in registry if hasattr(i, '_notify_revert')]:
        obj._notify_revert()

def reset():
    for obj in [i for i in registry if hasattr(i, '_notify_reset')]:
        obj._notify_reset()