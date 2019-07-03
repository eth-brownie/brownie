#!/usr/bin/python3

from .convert import Wei


class StrictDict(dict):
    '''Dict subclass that prevents adding new keys when locked'''

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
        '''Locks the dict so that new keys cannot be added'''
        for v in [i for i in self.values() if type(i) is StrictDict]:
            v._lock()
        self._locked = True

    def _unlock(self):
        '''Unlocks the dict so that new keys can be added'''
        for v in [i for i in self.values() if type(i) is StrictDict]:
            v._unlock()
        self._locked = False


class KwargTuple:
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


def _kwargtuple_compare(a, b):
    if type(a) not in (tuple, list, KwargTuple):
        types_ = set([type(a), type(b)])
        if dict in types_:
            return a == b
        if types_.intersection([bool, type(None)]):
            return a is b
        return _convert_str(a) == _convert_str(b)
    if type(b) not in (tuple, list, KwargTuple) or len(b) != len(a):
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


class FalseyDict(dict):
    '''Dict subclass that returns None if a key is not present instead of raising'''

    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        return None

    def _update_from_args(self, values):
        '''Updates the dict from docopts.args'''
        self.update(dict((k.lstrip("-"), v) for k, v in values.items()))

    def copy(self):
        return FalseyDict(self)


class EventDict:
    '''Dict/list hybrid container, base class for all events fired in a transaction.'''

    def __init__(self, events):
        '''Instantiates the class.

        Args:
            events: event data as supplied by eth_event.decode_logs or eth_event.decode_trace'''
        self._ordered = [_EventItem(
            i['name'],
            [dict((x['name'], x['value']) for x in i['data'])],
            (pos,)
        ) for pos, i in enumerate(events)]
        self._dict = {}
        for event in self._ordered:
            if event.name in self._dict:
                continue
            events = [i for i in self._ordered if i.name == event.name]
            self._dict[event.name] = _EventItem(
                event.name,
                events,
                tuple(i.pos[0] for i in events)
            )

    def __repr__(self):
        return str(self)

    def __bool__(self):
        return bool(self._ordered)

    def __contains__(self, name):
        '''returns True if an event fired with the given name.'''
        return name in [i.name for i in self._ordered]

    def __getitem__(self, key):
        '''if key is int: returns the n'th event that was fired
        if key is str: returns a _EventItem dict of all events where name == key'''
        if type(key) is int:
            return self._ordered[key]
        return self._dict[key]

    def __iter__(self):
        return iter(self._ordered)

    def __len__(self):
        '''returns the number of events that fired.'''
        return len(self._ordered)

    def __str__(self):
        return str(dict((k, [i[0] for i in v._ordered]) for k, v in self._dict.items()))

    def count(self, name):
        '''EventDict.count(name) -> integer -- return number of occurrences of name'''
        return len([i.name for i in self._ordered if i.name == name])

    def items(self):
        '''EventDict.items() -> a set-like object providing a view on EventDict's items'''
        return self._dict.items()

    def keys(self):
        '''EventDict.keys() -> a set-like object providing a view on EventDict's keys'''
        return self._dict.keys()

    def values(self):
        '''EventDict.values() -> an object providing a view on EventDict's values'''
        return self._dict.values()


class _EventItem:
    '''Dict/list hybrid container, represents one or more events with the same name
    that were fired in a transaction.

    Attributes:
        name: event name
        pos: tuple of indexes where this event fired'''

    def __init__(self, name, event_data, pos):
        self.name = name
        self._ordered = event_data
        self.pos = pos

    def __getitem__(self, key):
        '''if key is int: returns the n'th event that was fired with this name
        if key is str: returns the value of data field 'key' from the 1st event
        within the container '''
        if type(key) is int:
            return self._ordered[key]
        return self._ordered[0][key]

    def __contains__(self, name):
        '''returns True if this event contains a value with the given name.'''
        return name in self._ordered[0]

    def __len__(self):
        '''returns the number of events held in this container.'''
        return len(self._ordered)

    def __repr__(self):
        return str(self)

    def __str__(self):
        if len(self._ordered) == 1:
            return str(self._ordered[0])
        return str([i[0] for i in self._ordered])

    def __iter__(self):
        return iter(self._ordered)

    def __eq__(self, other):
        return other == self._ordered

    def items(self):
        '''_EventItem.items() -> a set-like object providing a view on _EventItem[0]'s items'''
        return self._ordered[0].items()

    def keys(self):
        '''_EventItem.keys() -> a set-like object providing a view on _EventItem[0]'s keys'''
        return self._ordered[0].keys()

    def values(self):
        '''_EventItem.values() -> an object providing a view on _EventItem[0]'s values'''
        return self._ordered[0].values()


class _Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
