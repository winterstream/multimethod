# Copyright (c) 2013, Wynand Winterbach
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice, this
#     list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#   * Neither the name of the Dojo Foundation nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__author__ = 'wynand'

import rwlock
import multimethod


class NilNode(object):
    pass


class ParentNotInHierarchy(Exception):
    pass


class ParentAlreadyInHierarchy(Exception):
    pass


class ChildAlreadyInHierarchy(Exception):
    pass


class Hierarchy(object):
    def __init__(self, root):
        self.root = root
        self.parent = {root: NilNode}
        self.ancestors = {root: {root}}  # Used to quickly answer is_a queries
        self.__version__ = 0
        self.rw = rwlock.ReadWriteLock()

    def _add_to_bottom(self, child, parent):
        if parent not in self.parent:
            raise ParentNotInHierarchy()
        self.ancestors[child] = self.ancestors[parent] | {child}
        self.parent[child] = parent
        self.__version__ += 1

    def _add_to_top(self, new_parent):
        if new_parent in self.parent:
            raise ParentAlreadyInHierarchy()
        old_parent = self.root
        self.parent[old_parent] = new_parent
        self.parent[new_parent] = NilNode
        self.ancestors[new_parent] = set()
        self.root = new_parent
        for ancestors in self.ancestors.viewvalues():
            ancestors.add(new_parent)
        self.__version__ += 1

    def add_new_root(self, new_root):
        with self.rw.write():
            self._add_to_top(new_root)

    def derive(self, child, parent):
        with self.rw.write():
            if child not in self.parent:
                self._add_to_bottom(child, parent)
            else:
                if self.parent[child] != parent:
                    raise ChildAlreadyInHierarchy()
                else:
                    # We allow existing derivations to be re-added
                    # as otherwise module reloading in Python would
                    # raise exceptions when derivations are re-added.
                    pass

    def is_a(self, child, parent):
        if isinstance(child, (str, unicode)):
            return parent in self.ancestors[child]
        else:
            try:
                child_seq = list(child)
                parent_seq = list(parent)
                if len(child_seq) == len(parent_seq):
                    return all(parent_seq[i] in self.ancestors[child_seq[i]]
                               for i in xrange(len(child_seq)))
                else:
                    return False
            except TypeError:
                try:
                    return parent in self.ancestors[child]
                except KeyError:
                    return False

    def multimethod(self, dispatch_func=lambda x: x, default_dispatch_val=multimethod.DefaultDispatchValue):
        def decorator(func):
            return multimethod.MultiMethod(func.__name__, dispatch_func, default_dispatch_val, self)
        return decorator
