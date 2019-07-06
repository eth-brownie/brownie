#!/usr/bin/python3

from brownie.cli.utils import color
from . import (
    pathutils,
    loader,
    output
)


def run_script(script_path, method_name="main", args=(), kwargs={}, gas_profile=False):
    '''Loads a project script and runs a method in it.

    script_path: path of script to load
    method_name: name of method to run
    args: method args
    kwargs: method kwargs
    gas_profile: if True, gas use data will be shown

    Returns: return value from called method
    '''
    script_path = pathutils.get_path(script_path, "scripts")
    module = loader.import_from_path(script_path)
    if not hasattr(module, method_name):
        raise AttributeError(f"Module '{module.__name__}' has no method '{method_name}'")
    print(
        f"\nRunning '{color['module']}{module.__name__}{color}."
        f"{color['callable']}{method_name}{color}'..."
    )
    result = getattr(module, method_name)(*args, **kwargs)
    if gas_profile:
        output.gas_profile()
    return result
