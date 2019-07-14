#!/usr/bin/python3

from copy import deepcopy

from brownie.convert import EthAddress, HexString, Wei


class ReturnValue:
    '''Tuple/dict hybrid container, used for return values on callable functions'''

    def __init__(self, values, abi):
        self._tuple = tuple(values)
        self._abi = abi
        self._dict = {}
        for c, i in enumerate(abi['outputs']):
            if not i['name']:
                continue
            self._dict[i['name']] = values[c]

    def __repr__(self):
        return repr(self._tuple)

    def __str__(self):
        return str(self._tuple)

    def __eq__(self, other):
        return _kwargtuple_compare(self, other)

    def __getitem__(self, key):
        if type(key) is slice:
            abi = deepcopy(self._abi)
            abi['outputs'] = abi['outputs'][key]
            return ReturnValue(self._tuple[key], abi)
        if type(key) is int:
            return self._tuple[key]
        return self._dict[key]

    def __contains__(self, value):
        return self.count(value) > 0

    def __iter__(self):
        return iter(self._tuple)

    def __len__(self):
        return len(self._tuple)

    def copy(self):
        '''ReturnValue.copy() -> a shallow copy of ReturnValue'''
        return ReturnValue(self._tuple, self._abi)

    def count(self, value):
        '''ReturnValue.count(value) -> integer -- return number of occurrences of value'''
        count = 0
        for item in self:
            try:
                if _kwargtuple_compare(item, value):
                    count += 1
            except TypeError:
                continue
        return count

    def dict(self):
        '''ReturnValue.dict() -> a dictionary of ReturnValue's named items'''
        return self._dict

    def index(self, value, start=0, stop=None):
        '''ReturnValue.index(value, [start, [stop]]) -> integer -- return first index of value.
        Raises ValueError if the value is not present.'''
        if stop is None:
            stop = len(self)
        for i in range(start, stop):
            try:
                if _kwargtuple_compare(self._tuple[i], value):
                    return i
            except TypeError:
                continue
        raise ValueError(f"{value} is not in ReturnValue")

    def items(self):
        '''ReturnValue.items() -> a set-like object providing a view on ReturnValue's named items'''
        return self._dict.items()

    def keys(self):
        '''ReturnValue.keys() -> a set-like object providing a view on ReturnValue's keys'''
        return self._dict.keys()


def _kwargtuple_compare(a, b):
    if type(a) not in (tuple, list, ReturnValue):
        types_ = set([type(a), type(b)])
        if types_.intersection([bool, type(None)]):
            return a is b
        if types_.intersection([dict, EthAddress, HexString]):
            return a == b
        return _convert_str(a) == _convert_str(b)
    if type(b) not in (tuple, list, ReturnValue) or len(b) != len(a):
        return False
    return next((False for i in range(len(a)) if not _kwargtuple_compare(a[i], b[i])), True)


def _convert_str(value):
    if type(value) is not str:
        if not hasattr(value, "address"):
            return value
        value = value.address
    if value.startswith("0x"):
        return "0x" + value.lstrip("0x").lower()
    if value.count(" ") != 1:
        return value
    try:
        return Wei(value)
    except ValueError:
        return value
