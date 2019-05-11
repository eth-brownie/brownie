#!/usr/bin/python3

from .convert import format_output


class StrictDict(dict):
    '''Dict subclass that prevents adding new keys when locked'''

    _print_as_dict = True

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

    _print_as_list = True

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


class FalseyDict(dict):
    '''Dict subclass that returns False if a key is not present'''

    _print_as_dict = True

    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        return False

    def _update_from_args(self, values):
        '''Updates the dict from docopts.args'''
        self.update(dict((k.lstrip("-"), v) for k, v in values.items()))

    def copy(self):
        return FalseyDict(self)


class EventDict:
    '''Dict/list hybrid container, base class for all events fired in a transaction.'''

    _print_as_dict = True

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
        if len(event_data) > 1:
            self._print_as_list = True
        else:
            self._print_as_dict = True

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
