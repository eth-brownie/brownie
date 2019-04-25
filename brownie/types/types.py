#!/usr/bin/python3


from .convert import format_output


# dict subclass that prevents adding new keys when locked
class StrictDict(dict):

    def __init__(self, values={}):
        self._locked = False
        super().__init__()
        self.update(values)

    def __setitem__(self, key, value):
        if self._locked and key not in self:
            raise KeyError("{} is not a known config setting".format(key))
        if type(value) is dict:
            value = StrictDict(value)
        super().__setitem__(key, value)

    def update(self, arg):
        for k, v in arg.items():
            self.__setitem__(k, v)

    def _lock(self):
        for v in [i for i in self.values() if type(i) is StrictDict]:
            v._lock()
        self._locked = True

    def _unlock(self):
        for v in [i for i in self.values() if type(i) is StrictDict]:
            v._unlock()
        self._locked = False


# dict container that returns False if key is not present
class FalseyDict:

    def __init__(self):
        self._dict = {}

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getitem__(self, key):
        if key in self._dict:
            return self._dict[key]
        return False


class KwargTuple:
    '''Tuple/dict hybrid class, used for return values on callable functions'''
    def __init__(self, values, abi):
        values = format_output(values)
        self._tuple = tuple(values)
        self._abi = abi
        self._dict = {}
        for c, i in enumerate(abi['outputs']):
            if not i['name']:
                continue
            self._dict[i['name']] = values[c]

    def _console_repr(self):
        return repr(self._tuple)

    def __str__(self):
        return str(self._tuple)

    def __eq__(self, other):
        return self._tuple == other

    def __getitem__(self, key):
        if type(key) in (int, slice):
            return self._tuple[key]
        return self._dict[key]

    def __contains__(self, value):
        return value in self._tuple

    def __iter__(self):
        return iter(self._tuple)

    def __len__(self):
        return len(self._tuple)

    def copy(self):
        '''KwargTuple.copy() -> a shallow copy of KwargTuple'''
        return KwargTuple(self._tuple, self._abi)

    def count(self, value):
        '''KwargTuple.count(value) -> integer -- return number of occurrences of value'''
        return self._tuple.count(value)

    def dict(self):
        '''KwargTuple.dict() -> a dictionary of KwargTuple's named items'''
        return self._dict

    def index(self, value, *args):
        '''KwargTuple.index(value, [start, [stop]]) -> integer -- return first index of value.
        Raises ValueError if the value is not present.'''
        return self._tuple.index(value, *args)

    def items(self):
        '''KwargTuple.items() -> a set-like object providing a view on KwargTuple's named items'''
        return self._dict.items()

    def keys(self):
        '''KwargTuple.keys() -> a set-like object providing a view on KwargTuple's keys'''
        return self._dict.values()


# dict container that returns False if key is not present
class FalseyDict:

    def __init__(self):
        self._dict = {}

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getitem__(self, key):
        if key in self._dict:
            return self._dict[key]
        return False

    def _update_from_args(self, values):
        self._dict.update(dict((k.replace('-',''),v) for k,v in values.items()))
