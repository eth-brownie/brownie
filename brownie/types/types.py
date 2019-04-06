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


# tuple/dict hybrid used for return values
class KwargTuple:

    def __init__(self, values, abi):
        values = format_output(values)
        self._tuple = tuple(values)
        self._abi = abi
        self._dict = {}
        for c, i in enumerate(abi['outputs']):
            if not i['name']:
                continue
            self._dict[i['name']] = values[c]
        for i in ('count', 'index'):
            setattr(self, i, getattr(self._tuple, i))
        for i in ('items', 'keys', 'values'):
            setattr(self, i, getattr(self._dict, i))

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
        return KwargTuple(self._tuple, self._abi)


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

