#!/usr/bin/python3

from collections import OrderedDict
import eth_event
import re

from lib.components.account import Accounts
from lib.components.compiler import add_contract
from lib.components.eth import web3, wei
from lib.components.transaction import TransactionReceipt, VirtualMachineError
from lib.components import config
CONFIG = config.CONFIG

class _ContractBase:

    def __init__(self, name, abi):
        self.abi = abi
        names = [i['name'] for i in abi if i['type']=="function"]
        duplicates = set(i for i in names if names.count(i)>1)
        if duplicates:
            raise AttributeError("Ambiguous contract functions in {}: {}".format(
                name, ",".join(duplicates)))
        self._name = name
        self.topics = eth_event.get_topics(abi)
        self.signatures = dict((
            i['name'],
            web3.sha3(text="{}({})".format(i['name'],
                ",".join(x['type'] for x in i['inputs'])
                )).hex()[:10]
        ) for i in abi if i['type']=="function")


class ContractDeployer(_ContractBase):

    def __init__(self, name, interface, network):
        self.tx = None
        self.bytecode = interface['bytecode']
        self._deployed = OrderedDict()
        self._network = network
        super().__init__(name, interface['abi'])
        for k, data in sorted([
            (k,v) for k,v in interface['networks'].items() if 
            v['network']==CONFIG['active_network']['name']
        ], key=lambda k: int(k[0])):
            if web3.eth.getCode(data['address']).hex() == "0x00":
                print("WARNING: No contract deployed at {}.".format(data['address']))
                continue
            self._deployed[data['address']] = Contract(
                data['address'],
                self._name,
                self.abi, data['owner'],
                (
                    TransactionReceipt(data['transactionHash'], silent=True)
                    if data['transactionHash'] else None
                )
            )
    
    def __iter__(self):
        return iter(self._deployed.values())

    def __getitem__(self, i):
        return list(self._deployed.values())[i]

    def __len__(self):
        return len(self._deployed)

    def __repr__(self):
        return "<{} ContractDeployer object>".format(self._name)

    def list(self):
        return list(self._deployed)

    def deploy(self, account, *args):
        if '_' in self.bytecode:
            for marker in re.findall('_{1,}[^_]*_{1,}', self.bytecode):
                contract = marker.strip('_')
                if contract not in self._network:
                    raise NameError(
                        "Contract requires an unknown library - " + contract
                    )
                elif not len(self._network[contract]):
                    raise IndexError(
                        "Contract requires the {} library but it has not been deployed yet".format(contract)
                    )
                bytecode = self.bytecode.replace(marker, self._network[contract][-1][-40:])
        else:
            bytecode = self.bytecode
        args, tx = _get_tx(account, args)
        contract = web3.eth.contract(abi = self.abi, bytecode = bytecode)
        try:
            types = [i['type'] for i in next(i for i in self.abi if i['type']=="constructor")['inputs']]
            args = _format_inputs("constructor", args, types)
        except StopIteration:
            if args:
                raise AttributeError("This contract takes no constructor arguments.")
        tx = account._contract_tx(contract.constructor, args, tx, self._name+".constructor", self._at)
        if tx.contract_address:
            return self.at(tx.contract_address)
        return tx
        
    def _at(self, tx):
        self.at(tx.contract_address, tx.sender, tx)

    
    def at(self, address, owner = None, tx = None):
        address = web3.toChecksumAddress(address)
        if address in self._deployed:
            return self._deployed[address]
        if web3.eth.getCode(address).hex() == "0x00":
            raise ValueError("No contract deployed at {}".format(address))
        self._deployed[address] = Contract(address, self._name, self.abi, owner, tx)
        if CONFIG['active_network']['persist']:
            add_contract(self._name, address, tx.hash if tx else None, owner)
        return self._deployed[address]
            

class Contract(str,_ContractBase):

    def __new__(cls, address, *args):
        return super().__new__(cls, address)

    def __init__(self, address, name, abi, owner, tx=None):
        super().__init__(name, abi)
        self.tx = tx
        self.bytecode = web3.eth.getCode(address).hex()[2:]
        self._owner = owner
        self._contract = web3.eth.contract(address = address, abi = abi)
        for i in [i for i in abi if i['type']=="function"]:
            if hasattr(self, i['name']):
                raise AttributeError("Namespace collision: '{}.{}'".format(name, i['name']))
            fn = getattr(self._contract.functions,i['name'])
            name = "{}.{}".format(self._name, i['name'])
            if i['stateMutability'] in ('view','pure'):
                setattr(self, i['name'], ContractCall(fn, i, name, owner))
            else:
                setattr(self, i['name'], ContractTx(fn, i, name, owner))
    
    def __repr__(self):
        return "<{0._name} Contract object '{0.address}'>".format(self)

    def __str__(self):
        return self.__repr__()

    def __getattr__(self, name):
        return getattr(self._contract, name)

    def balance(self):
        return web3.eth.getBalance(self._contract.address)

class _ContractMethod:

    def __init__(self, fn, abi, name, owner):
        self._fn = fn
        self._name = name
        self.abi = abi
        self._owner = owner
        self.signature = web3.sha3(text="{}({})".format(
            abi['name'],
            ",".join(i['type'] for i in abi['inputs'])
            )).hex()[:10]

    def __repr__(self):
        return "<{} object '{}({})'>".format(
            type(self).__name__,
            self.abi['name'],
            ",".join(i['type'] for i in self.abi['inputs']))
    
    def _format_inputs(self, args):
        types = [i['type'] for i in self.abi['inputs']]
        return _format_inputs(self.abi['name'], args, types)

class ContractTx(_ContractMethod):

    def __call__(self, *args):
        args, tx = _get_tx(self._owner, args)
        if not tx['from']:
            raise AttributeError(
                "Contract has no owner, you must supply a tx dict with a 'from'"
                " field as the last argument.")
        return tx['from']._contract_tx(self._fn, self._format_inputs(args), tx, self._name)

class ContractCall(_ContractMethod):

    def __call__(self, *args):
        try: 
            result = self._fn(*self._format_inputs(args)).call()
        except ValueError as e:
            raise VirtualMachineError(e)
        if type(result) is not list:
            return web3.toHex(result) if type(result) is bytes else result
        return [(web3.toHex(i) if type(i) is bytes else i) for i in result]


def _get_tx(owner, args):
        if args and type(args[-1]) is dict:
            args, tx = (args[:-1], args[-1])
            if 'from' not in tx:
                tx['from'] = owner
            for key in [i for i in ['value','gas','gasPrice'] if i in tx]:
                tx[key] = wei(tx[key])
        else:
            tx = {'from': owner}
        return args, tx

def _format_inputs(name, inputs, types):
        inputs = list(inputs)
        if len(inputs) != len(types):
            raise AttributeError(
                "{} requires the following arguments: {}".format(
                name,",".join(types)))
        for i, type_ in enumerate(types):
            if type_[-1]=="]":
                t,length = type_.rstrip(']').rsplit('[', maxsplit=1)
                if length != "" and len(inputs[i]) != int(length):
                    raise ValueError(
                        "'{}': Argument {}, sequence has a length of {}, should be {}".format(
                            name, i, len(inputs[i]), type_))
                inputs[i] = _format_inputs(name, inputs[i],[t]*len(inputs[i]))
                continue
            try:
                if "int" in type_:
                    inputs[i] = wei(inputs[i])
                elif "bytes" in type_ and type(inputs[i]) is not bytes:
                    if type(inputs[i]) is not str:
                        inputs[i]=int(inputs[i]).to_bytes(int(type_[5:]),"big")
                    elif inputs[i][:2]!="0x":
                        inputs[i]=inputs[i].encode() 
            except:
                raise ValueError(
                    "'{}': Argument {}, could not convert {} '{}' to type {}".format(
                        name,i,type(inputs[i]).__name__,inputs[i],type_))
        return inputs