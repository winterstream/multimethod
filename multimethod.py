# Copyright (c) Rich Hickey & Wynand Winterbach. All rights reserved.
# The use and distribution terms for this software are covered by the
# Eclipse Public License 1.0 (http://opensource.org/licenses/eclipse-1.0.php)
# which can be found in the file epl-v10.html at the root of this distribution.
# By using this software in any fashion, you are agreeing to be bound by
# the terms of this license.
# You must not remove this notice, or any other, from this software.

import rwlock
import versioneddict


class DefaultDispatchValue(object):
    pass


class ArgumentConflict(Exception):
    pass


class PreferenceConflict(Exception):
    pass


class MultiMethod(object):
    def __init__(self, name, dispatch_func, default_dispatch_val=DefaultDispatchValue, hierarchy=None, default_func=None):
        self.rw = rwlock.ReadWriteLock()
        self.name = name

        self.dispatch_func = dispatch_func
        self.default_dispatch_val = default_dispatch_val

        self.hierarchy_version = hierarchy.__version__
        self.hierarchy = hierarchy

        self.method_table = versioneddict.VersionedOrderedDict()
        self.prefer_table = versioneddict.VersionedOrderedDict()

        if default_func is not None:
            self.method_table[default_dispatch_val] = default_func

        self.method_cache = {}

    def _reset_cache(self):
        # You must hold a write lock for this object and a read lock on hierarchy to call this
        self.method_cache.clear()
        self.hierarchy_version = self.hierarchy.__version__

    def _prefers(self, x, y):
        # You must hold at least a read lock before calling this
        try:
            return y in self.prefer_table[x]
        except KeyError:
            return False

    def _dominates(self, x, y):
        # To call this, you must call a read
        return self.hierarchy.is_a(x, y) or self._prefers(x, y)

    def _find_and_cache_best_method(self, dispatch_val):
        while True:
            h = self.hierarchy
            with self.rw.read(), h.rw.read():
                best_match_dispatch_val = None
                best_match_method = None
                method_table_version = self.method_table.__version__
                prefer_table_version = self.prefer_table.__version__

                for other_dispatch_val, other_method in self.method_table.iteritems():
                    if h.is_a(dispatch_val, other_dispatch_val):
                        if (best_match_dispatch_val is None
                                or self._dominates(other_dispatch_val, best_match_dispatch_val)):
                            best_match_dispatch_val = other_dispatch_val
                            best_match_method = other_method
                        if not self._dominates(best_match_dispatch_val, other_dispatch_val):
                            raise ArgumentConflict("Multiple methods in multimethod '{0}' match dispatch value: " \
                                            "{1} -> {2} and {3}, and neither is preferred",
                                            self.name, dispatch_val, other_dispatch_val, best_match_dispatch_val)

                if best_match_dispatch_val is None:
                    return None

            with self.rw.write(), self.hierarchy.rw.read():
                if (self.method_table.__version__ == method_table_version
                        and self.prefer_table.__version__ == prefer_table_version
                        and self.hierarchy_version == self.hierarchy.__version__):
                    self.method_cache[dispatch_val] = best_match_method
                    return best_match_method
                else:
                    self._reset_cache()

    def get_method(self, dispatch_val):
        # It could happen that the hierarchy is in the process of
        # being modified when we check this. However, this must happen
        # in another thread and we cannot be bothered. The worst that
        # can happen is that the other method clears method_cache
        # before we get there (first statement after this conditional).
        # Should that happen, target_func will be assigned None and
        # we'll have to dive into _find_and_cache_best_method.
        # But won't it be bad if we get to method_cache *before*
        # it is cleared in the event that someone modified the
        # hierarchy or added/removed a method? No, no, no. That
        # must happen in another thread and there are no guarantees
        # about synchronization. You should arrange for such
        # synchronization if it is important for your application.
        if self.hierarchy_version != self.hierarchy.__version__:
            with self.rw.write(), self.hierarchy.rw.read():
                self._reset_cache()
        target_func = self.method_cache.get(dispatch_val, None)
        if target_func is not None:
            return target_func
        target_func = self._find_and_cache_best_method(dispatch_val)
        if target_func is not None:
            return target_func
        try:
            return self.method_table[self.default_dispatch_val]
        except KeyError:
            raise NotImplementedError("No method in multimethod '{0}' for dispatch value: {1}".format(
                self.name, dispatch_val))

    def __call__(self, *args, **kwargs):
        return self.get_method(self.dispatch_func(*args, **kwargs))(*args, **kwargs)

    def prefer_method(self, dispatch_val_x, dispatch_val_y):
        if isinstance(dispatch_val_x, list):
            dispatch_val_x = tuple(dispatch_val_x)
        if isinstance(dispatch_val_y, list):
            dispatch_val_y = tuple(dispatch_val_y)
        with self.rw.write(), self.hierarchy.rw.read():
            if self._prefers(dispatch_val_y, dispatch_val_x):
                raise PreferenceConflict("Preference conflict in multimethod '{0}': {1} is already preferred over {2}".format(
                    self.name, dispatch_val_y, dispatch_val_x))
            try:
                self.prefer_table[dispatch_val_x].add(dispatch_val_y)
            except KeyError:
                self.prefer_table[dispatch_val_x] = {dispatch_val_y}
            self._reset_cache()
            return self

    def add_method(self, dispatch_val):
        if isinstance(dispatch_val, list):
            dispatch_val = tuple(dispatch_val)

        def decorator(func):
            with self.rw.write(), self.hierarchy.rw.read():
                self.method_table[dispatch_val] = func
                self._reset_cache()
                return self
        return decorator

    def remove_method(self, dispatch_val):
        with self.rw.write(), self.hierarchy.rw.read():
            del self.method_table[dispatch_val]
            self._reset_cache()
            return self
