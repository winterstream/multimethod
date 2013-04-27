__author__ = 'wynand'

from collections import OrderedDict


class VersionedOrderedDict(OrderedDict):
    def __init__(self, *args, **kwargs):
        super(VersionedOrderedDict, self).__init__(*args, **kwargs)
        self.__version__ = 0

    def __setitem__(self, key, value):
        super(VersionedOrderedDict, self).__setitem__(key, value)
        self.__version__ += 1

    def __delitem__(self, key):
        super(VersionedOrderedDict, self).__delitem__(key)
        self.__version__ += 1

    def clear(self):
        super(VersionedOrderedDict, self).clear()
        self.__version__ += 1

    def update(self, E=None, **F):
        super(VersionedOrderedDict, self).update(E, **F)
        self.__version__ += 1

    def pop(self, key, **kwargs):
        super(VersionedOrderedDict, self).popitem(key, **kwargs)
        self.__version__ += 1

    def popitem(self, last=True):
        super(VersionedOrderedDict, self).pop(last)
        self.__version__ += 1

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = default

