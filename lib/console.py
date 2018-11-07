#!/usr/bin/python3

import importlib
import json
import os
import readline
import sys
import traceback

from lib.services.fernet import FernetKey

if "--help" in sys.argv:
    sys.exit("""Usage: brownie console [options]

Options:
  --gas              Show gas costs for each successful transaction
  --network [name]   Use a specific network outlined in config.json (default development)

TODO - Write some stuff here""")

sys.path.insert(0, "")


from lib.components.network import Network

network = Network()
accounts = network.accounts

while True:
    cmd = input('>>> ')
    if cmd == "exit()": sys.exit()
    if cmd.split(' ')[0] == "deploy":
        cmd = cmd.split(' ')[1]
        _module = importlib.import_module("deployments."+cmd)
        print("Running deployment script '{}'...".format(cmd))
        try:
            _module.deploy(network, network.accounts)
            print("Deployment of '{}' was successful.".format(cmd))
        except Exception as e:
            print("ERROR: Deployment of '{}' failed due to {} - {}".format(
                    cmd, type(e).__name__, e))
        continue
    if cmd[:13] == "save accounts":
        to_save = [i._priv_key for i in accounts if hasattr(i, '_priv_key')]
        filename, pwd = cmd.split(' ', maxsplit=4)[2:]
        encrypted = FernetKey(pwd).encrypt(json.dumps(to_save), False)
        open(filename+".acc", 'w').write(encrypted)
        print("Local accounts saved as {}.acc".format(filename))
        continue
    if cmd[:13] == "load accounts":
        filename, pwd = cmd.split(' ', maxsplit=4)[2:]
        encrypted = open(filename+".acc","r").read()
        decrypted = json.loads(FernetKey(pwd).decrypt(encrypted))
        for i in decrypted:
            network.add_account(i)
        print("Local accounts loaded from {}.acc".format(filename))
        continue
    _exec_result = None
    cmd = "_exec_result = "+cmd
    try:
        exec(cmd)
        if _exec_result != None:
            print(_exec_result)
    except:
        print("{}{}: {}".format(
                ''.join(traceback.format_tb(sys.exc_info()[2])),
                sys.exc_info()[0].__name__, sys.exc_info()[1]))
